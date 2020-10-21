"""
“Copyright 2020 LiberaForms.org”

This file is part of LiberaForms.

LiberaForms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json, datetime
from threading import Thread
from flask import g, request, render_template, redirect
from flask import session, flash, send_file, after_this_request
from flask import Blueprint
from flask_babel import gettext

from liberaforms import app, csrf
from liberaforms.models.form import Form
from liberaforms.models.user import User
from liberaforms.utils.wraps import *
from liberaforms.utils import form_helper
from liberaforms.utils import sanitizers
from liberaforms.utils import validators
from liberaforms.utils.email import EmailServer
from liberaforms.utils.consent_texts import ConsentText
from liberaforms.utils.utils import make_url_for, JsonResponse, gen_random_string, logout_user
import liberaforms.utils.wtf as wtf

#from pprint import pprint as pp

form_bp = Blueprint('form_bp', __name__,
                    template_folder='../templates/form')


@form_bp.route('/forms', methods=['GET'])
@enabled_user_required
def my_forms():
    return render_template( 'my-forms.html', user=g.current_user) 

"""
@form_bp.route('/forms/templates', methods=['GET'])
@login_required
def list_form_templates():
    return render_template('form_templates.html', templates=formTemplates)
"""

@form_bp.route('/forms/new', methods=['GET'])
@form_bp.route('/forms/new/<string:templateID>', methods=['GET'])
@enabled_user_required
def new_form(templateID=None):
    form_helper.clear_session_form_data()
    session['introductionTextMD'] = Form.defaultIntroductionText()
    return render_template('edit-form.html', host_url=g.site.host_url)


@form_bp.route('/forms/edit', methods=['GET', 'POST'])
@form_bp.route('/forms/edit/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def edit_form(id=None):
    queriedForm=None
    if id:
        if session['form_id'] != id:
            flash(gettext("Something went wrong. id does not match session['form_id']"), 'error')
            return redirect(make_url_for('form_bp.my_forms'))            
        queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
        if not queriedForm:
            flash(gettext("You can't edit that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm:
            session['slug'] = queriedForm.slug
        elif 'slug' in request.form:
            session['slug'] = sanitizers.sanitize_slug(request.form['slug'])
        if not session['slug']:
            flash(gettext("Something went wrong. No slug!"), 'error')
            return redirect(make_url_for('form_bp.my_forms'))
        structure = form_helper.repair_form_structure(json.loads(request.form['structure']))
        session['formStructure'] = json.dumps(structure)
        session['formFieldIndex'] = Form.createFieldIndex(structure)
        session['introductionTextMD'] = sanitizers.escape_markdown(
                                                request.form['introductionTextMD'])
        return redirect(make_url_for('form_bp.preview_form'))
    optionsWithData = queriedForm.getMultichoiceOptionsWithSavedData() if queriedForm else {}
    return render_template('edit-form.html',    host_url=g.site.host_url,
                                                multichoiceOptionsWithSavedData=optionsWithData)


@form_bp.route('/forms/check-slug-availability', methods=['POST'])
@enabled_user_required
def is_slug_available():    
    if 'slug' in request.form and request.form['slug']:
        slug=request.form['slug']
    else:
        return JsonResponse(json.dumps({'slug':"", 'available':False}))
    available = True
    slug=sanitizers.sanitize_slug(slug)
    if not slug:
        available = False
    elif Form.find(slug=slug, hostname=g.site.hostname):
        available = False
    elif slug in app.config['RESERVED_SLUGS']:
        available = False
    # we return a sanitized slug as a suggestion for the user.
    return JsonResponse(json.dumps({'slug':slug, 'available':available}))


@form_bp.route('/forms/preview', methods=['GET'])
@enabled_user_required
def preview_form():
    if not ('slug' in session and 'formStructure' in session):
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template( 'preview-form.html',
                            slug=session['slug'],
                            introductionText=sanitizers.markdown2HTML(
                                                            session['introductionTextMD']))


@form_bp.route('/forms/edit/conditions/<string:id>', methods=['GET'])
@enabled_user_required
def conditions_form(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    #pp(queriedForm.structure)
    return render_template('conditions.html', form=queriedForm)


@form_bp.route('/forms/save', methods=['POST'])
@form_bp.route('/forms/save/<string:id>', methods=['POST'])
@enabled_user_required
def save_form(id=None):    
    if 'structure' in request.form:
        structure = form_helper.repair_form_structure(json.loads(request.form['structure']))
        session['formStructure'] = json.dumps(structure)
        session['formFieldIndex'] = Form.createFieldIndex(structure)
    if 'introductionTextMD' in request.form:
        session['introductionTextMD'] = sanitizers.escape_markdown(
                                                        request.form['introductionTextMD'])
    
    formStructure = json.loads(session['formStructure'])
    if not formStructure:
        formStructure=[{'label': gettext("Form"), 'subtype': 'h1', 'type': 'header'}]
    introductionText={  'markdown':sanitizers.escape_markdown(session['introductionTextMD']),
                        'html':sanitizers.markdown2HTML(session['introductionTextMD'])}
    
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id)) if id else None    
    if queriedForm:
        queriedForm.structure=formStructure
        queriedForm.updateFieldIndex(session['formFieldIndex'])
        queriedForm.updateExpiryConditions()
        queriedForm.introductionText=introductionText
        queriedForm.save()
        form_helper.clear_session_form_data()
        flash(gettext("Updated form OK"), 'success')
        queriedForm.addLog(gettext("Form edited"))
        return redirect(make_url_for('form_bp.inspect_form', id=queriedForm.id))
    else:
        # this is a new form
        if not session['slug']:
            # just in case!
            flash(gettext("Slug is missing."), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        if Form.find(slug=session['slug'], hostname=g.site.hostname):
            flash(gettext("Slug is not unique. %s" % (session['slug'])), 'error')
            return redirect(make_url_for('form_bp.edit_form'))
        if session['duplication_in_progress']:
            # this new form is a duplicate
            consentTexts=session['consentTexts']
            afterSubmitText=session['afterSubmitText']
            expiredText=session['expiredText']
        else:
            consentTexts=[Form.newDataConsent()]
            afterSubmitText={'html':"", 'markdown':""}
            expiredText={'html':"", 'markdown':""}
        #pp(formStructure)
        
        newFormData={
                    "created": datetime.date.today().strftime("%Y-%m-%d"),
                    "author_id": str(g.current_user.id),
                    "editors": {str(g.current_user.id): Form.newEditorPreferences(g.current_user)},
                    "postalCode": "08014",
                    "enabled": False,
                    "expired": False,
                    "expiryConditions": {"expireDate": False, "fields": {}},
                    "hostname": g.site.hostname,
                    "slug": session['slug'],
                    "structure": formStructure,
                    "fieldIndex": session['formFieldIndex'],
                    "sharedEntries": {  "enabled": False,
                                        "key": gen_random_string(),
                                        "password": False,
                                        "expireDate": False},
                    "introductionText": introductionText,
                    "consentTexts": consentTexts,
                    "afterSubmitText": afterSubmitText,
                    "expiredText": expiredText,
                    "sendConfirmation": Form.structureHasEmailField(formStructure),
                    "log": [],
                    "restrictedAccess": False,
                    "adminPreferences": { "public": True }
                }
        newForm=Form.saveNewForm(newFormData)
        form_helper.clear_session_form_data()
        newForm.addLog(gettext("Form created"))
        flash(gettext("Saved form OK"), 'success')
        # notify form.site.admins
        thread = Thread(target=EmailServer().sendNewFormNotification(newForm))
        thread.start()
        return redirect(make_url_for('form_bp.inspect_form', id=newForm.id))


@form_bp.route('/forms/save-consent/<string:form_id>/<string:consent_id>', methods=['POST'])
@enabled_user_required
def save_data_consent(form_id, consent_id):
    queriedForm = Form.find(id=form_id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "Info: Queried form not found", 'markdown': "", "label": ""}))
    if 'markdown' in request.form and "label" in request.form and "required" in request.form:
        consent = queriedForm.saveConsent(consent_id, data=request.form.to_dict(flat=True))
        if consent:
            return JsonResponse(json.dumps(consent))
    return JsonResponse(json.dumps({'html': "<h1>%s</h1>" % gettext("An error occured"),"label":""}))


@form_bp.route('/forms/default-consent/<string:form_id>/<string:consent_id>', methods=['GET'])
@enabled_user_required
def default_consent_text(form_id, consent_id):
    queriedForm = Form.find(id=form_id, editor_id=str(g.current_user.id))
    if queriedForm:
        return JsonResponse(json.dumps(queriedForm.site.getConsentForDisplay(consent_id)))
    return JsonResponse(json.dumps({'html': "<h1>%s</h1>" % gettext("An error occured"),"label":""}))


@form_bp.route('/forms/save-after-submit-text/<string:id>', methods=['POST'])
@enabled_user_required
def save_after_submit_text(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "", 'markdown': ""}))
    if 'markdown' in request.form:
        queriedForm.saveAfterSubmitText(request.form['markdown'])
        return JsonResponse(json.dumps({'html':queriedForm.afterSubmitTextHTML,
                                        'markdown': queriedForm.afterSubmitTextMarkdown}))
    return JsonResponse(json.dumps({'html': "<h1>%s</h1>" % gettext("An error occured"), 'markdown': ""}))


@form_bp.route('/forms/save-expired-text/<string:id>', methods=['POST'])
@enabled_user_required
def save_expired_text(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps({'html': "", 'markdown': ""}))
    if 'markdown' in request.form:
        queriedForm.saveExpiredText(request.form['markdown'])
        return JsonResponse(json.dumps({'html': queriedForm.expiredTextHTML,
                                        'markdown': queriedForm.expiredTextMarkdown}))
    return JsonResponse(json.dumps({'html': "<h1>%s</h1>" % gettext("An error occured"), 'markdown': ""}))


@form_bp.route('/forms/delete/<string:id>', methods=['GET', 'POST'])
@enabled_user_required
def delete_form(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    if request.method == 'POST':
        if queriedForm.slug == request.form['slug']:
            entry_cnt = queriedForm.getEntries().count()
            queriedForm.deleteForm()
            flash(gettext("Deleted '%s' and %s entries" % (queriedForm.slug, entry_cnt)), 'success')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            flash(gettext("Form name does not match"), 'warning')
    return render_template('delete-form.html', form=queriedForm)


@form_bp.route('/forms/view/<string:id>', methods=['GET'])
@enabled_user_required
def inspect_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    #print(queriedForm)
    if not g.current_user.can_inspect_form(queriedForm):
        flash(gettext("Permission needed to view form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    form_helper.populate_session_with_form(queriedForm) # prepare the session for possible form edit.
    return render_template('inspect-form.html', form=queriedForm)


@form_bp.route('/forms/share/<string:id>', methods=['GET'])
@enabled_user_required
def share_form(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('share-form.html', form=queriedForm, wtform=wtf.GetEmail())


@form_bp.route('/forms/add-editor/<string:id>', methods=['POST'])
@enabled_user_required
def add_editor(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    wtform=wtf.GetEmail()
    if wtform.validate():
        newEditor=User.find(email=wtform.email.data, hostname=queriedForm.hostname)
        if not newEditor or newEditor.enabled==False:
            flash(gettext("Can't find a user with that email"), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))
        if str(newEditor.id) in queriedForm.editors:
            flash(gettext("%s is already an editor" % newEditor.email), 'warning')
            return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))
        
        if queriedForm.addEditor(newEditor):
            flash(gettext("New editor added ok"), 'success')
            queriedForm.addLog(gettext("Added editor %s" % newEditor.email))
    return redirect(make_url_for('form_bp.share_form', id=queriedForm.id))


@form_bp.route('/forms/remove-editor/<string:form_id>/<string:editor_id>', methods=['POST'])
@enabled_user_required
def remove_editor(form_id, editor_id):
    queriedForm = Form.find(id=form_id, editor_id=str(g.current_user.id))
    editor = User.find(id=editor_id)
    if queriedForm and editor and not queriedForm.isAuthor(editor):
        queriedForm.removeEditor(editor)
        queriedForm.addLog(gettext("Removed editor %s" % editor.email))
        return json.dumps(str(editor.id))
    return json.dumps(False)


@form_bp.route('/forms/expiration/<string:id>', methods=['GET'])
@enabled_user_required
def expiration(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('expiration.html', form=queriedForm)


@form_bp.route('/forms/set-expiration-date/<string:id>', methods=['POST'])
@enabled_user_required
def set_expiration_date(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    if 'date' in request.form and 'time' in request.form:
        if request.form['date'] and request.form['time']:
            expireDate="%s %s:00" % (request.form['date'], request.form['time'])
            if not validators.is_valid_date(expireDate):
                return JsonResponse(json.dumps({'error': gettext("Date-time is not valid"),
                                                'expired': queriedForm.hasExpired()}))
            else:
                queriedForm.expiryConditions['expireDate']=expireDate
                queriedForm.expired=queriedForm.hasExpired()
                queriedForm.save()
                queriedForm.addLog(gettext("Expiry date set to: %s" % expireDate))
        elif not request.form['date'] and not request.form['time']:
            if queriedForm.expiryConditions['expireDate']:
                queriedForm.expiryConditions['expireDate']=False
                queriedForm.expired=queriedForm.hasExpired()
                queriedForm.save()
                queriedForm.addLog(gettext("Expiry date cancelled"))
        else:
            return JsonResponse(json.dumps({'error': gettext("Missing date or time"),
                                            'expired': queriedForm.hasExpired()}))
        return JsonResponse(json.dumps({'expired': queriedForm.hasExpired()}))


@form_bp.route('/forms/set-field-condition/<string:id>', methods=['POST'])
@enabled_user_required
def set_field_condition(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps({'condition': False}))

    availableFields=queriedForm.getAvailableNumberTypeFields()
    if not request.form['field_name'] in availableFields:
        return JsonResponse(json.dumps({'condition': False, 'expired': queriedForm.expired}))
    
    if not request.form['condition']:
        if request.form['field_name'] in queriedForm.fieldConditions:
            del queriedForm.fieldConditions[request.form['field_name']]
            queriedForm.expired=queriedForm.hasExpired()
            queriedForm.save()
        return JsonResponse(json.dumps({'condition': False, 'expired': queriedForm.expired}))
    
    fieldType=availableFields[request.form['field_name']]['type']
    if fieldType == "number":
        try:
            queriedForm.fieldConditions[request.form['field_name']]={
                                                            "type": fieldType,
                                                            "condition": int(request.form['condition'])
                                                            }
            queriedForm.expired=queriedForm.hasExpired()
            queriedForm.save()
        except:
            return JsonResponse(json.dumps({'condition': False, 'expired': queriedForm.hasExpired()}))
    return JsonResponse(    json.dumps({'condition': request.form['condition'],
                            'expired': queriedForm.expired}) )


@form_bp.route('/forms/duplicate/<string:id>', methods=['GET'])
@enabled_user_required
def duplicate_form(id):
    queriedForm = Form.find(id=id)
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    form_helper.populate_session_with_form(queriedForm)
    session['slug']=""
    session['form_id']=None
    session['duplication_in_progress'] = True
    flash(gettext("You can edit the duplicate now"), 'info')
    return render_template('edit-form.html', host_url=g.site.host_url)


@form_bp.route('/forms/log/list/<string:id>', methods=['GET'])
@enabled_user_required
def list_log(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        flash(gettext("Can't find that form"), 'warning')
        return redirect(make_url_for('form_bp.my_forms'))
    return render_template('list-log.html', form=queriedForm)



""" Form settings """

@form_bp.route('/form/toggle-enabled/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_enabled(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    enabled=queriedForm.toggleEnabled()
    queriedForm.addLog(gettext("Public set to: %s" % enabled))
    return JsonResponse(json.dumps({'enabled': enabled}))


@form_bp.route('/form/toggle-shared-entries/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_shared_entries(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    shared=queriedForm.toggleSharedEntries()
    queriedForm.addLog(gettext("Shared entries set to: %s" % shared))
    return JsonResponse(json.dumps({'enabled':shared}))


@form_bp.route('/form/toggle-restricted-access/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_restricted_access(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    access=queriedForm.toggleRestrictedAccess()
    queriedForm.addLog(gettext("Restricted access set to: %s" % access))
    return JsonResponse(json.dumps({'restricted':access}))


@form_bp.route('/form/toggle-notification/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_notification(id):
    editor_id=str(g.current_user.id)
    queriedForm = Form.find(id=id, editor_id=editor_id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    return JsonResponse(json.dumps({'notification':queriedForm.toggleNotification(editor_id)}))


@form_bp.route('/form/toggle-data-consent/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_dataconsent(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    dataConsentBool=queriedForm.toggleDataConsentEnabled()
    queriedForm.addLog(gettext("Data protection consent set to: %s" % dataConsentBool))
    return JsonResponse(json.dumps({'enabled':dataConsentBool}))


@form_bp.route('/form/toggle-send-confirmation/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_sendconfirmation(id):
    queriedForm = Form.find(id=id, editor_id=str(g.current_user.id))
    if not queriedForm:
        return JsonResponse(json.dumps())
    sendConfirmationBool=queriedForm.toggleSendConfirmation()
    queriedForm.addLog(gettext("Send Confirmation set to: %s" % sendConfirmationBool))
    return JsonResponse(json.dumps({'confirmation':sendConfirmationBool}))


@form_bp.route('/form/toggle-expiration-notification/<string:id>', methods=['POST'])
@enabled_user_required
def toggle_form_expiration_notification(id):
    editor_id=str(g.current_user.id)
    queriedForm = Form.find(id=id, editor_id=editor_id)
    if not queriedForm:
        return JsonResponse(json.dumps())
    return JsonResponse(json.dumps({
            'notification':queriedForm.toggleExpirationNotification(editor_id) }))
    

@form_bp.route('/embed/<string:slug>', methods=['GET', 'POST'])
@csrf.exempt
@sanitized_slug_required
def view_embedded_form(slug):
    logout_user()
    g.embedded=True
    return view_form(slug=slug)

@form_bp.route('/<string:slug>', methods=['GET', 'POST'])
@sanitized_slug_required
def view_form(slug):
    queriedForm = Form.find(slug=slug, hostname=g.site.hostname)
    if not queriedForm:
        if g.current_user:
            flash(gettext("Can't find that form"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        else:
            return render_template('page-not-found.html'), 400
    if not queriedForm.isPublic():
        if g.current_user:
            if queriedForm.expired:
                flash(gettext("That form has expired"), 'warning')
            else:
                flash(gettext("That form is not public"), 'warning')
            return redirect(make_url_for('form_bp.my_forms'))
        if queriedForm.expired:
            return render_template('form-has-expired.html', form=queriedForm), 400
        else:
            return render_template('page-not-found.html'), 400
    if queriedForm.restrictedAccess and not g.current_user:
        return render_template('page-not-found.html'), 400

    if request.method == 'POST':
        formData=request.form.to_dict(flat=False)
        entry = {'marked': False}
        for key in formData:
            if key=='csrf_token':
                continue
            value = formData[key]
            if isinstance(value, list): # A checkboxes-group contains multiple values 
                value=', '.join(value) # convert list of values to a string
                key=key.rstrip('[]') # remove tailing '[]' from the name attrib (appended by formbuilder)
            value=sanitizers.remove_first_and_last_newlines(value.strip())
            entry[key]=value
        queriedForm.addEntry(entry)
        
        if not queriedForm.expired and queriedForm.hasExpired():
            queriedForm.expired=True
            emails=[]
            for editor_id, preferences in queriedForm.editors.items():
                if preferences["notification"]["expiredForm"]:
                    user=User.find(id=editor_id)
                    if user and user.enabled:
                        emails.append(user.email)
            if emails:
                def sendExpiredFormNotification():
                    EmailServer().sendExpiredFormNotification(emails, queriedForm)
                thread = Thread(target=sendExpiredFormNotification())
                thread.start()
        queriedForm.save()
        
        if queriedForm.mightSendConfirmationEmail() and 'send-confirmation' in formData:
            confirmationEmail=queriedForm.getConfirmationEmailAddress(entry)
            if confirmationEmail and validators.is_valid_email(confirmationEmail):
                def sendConfirmation():
                    print("send")
                    EmailServer().sendConfirmation(confirmationEmail, queriedForm)
                thread = Thread(target=sendConfirmation())
                thread.start()

        emails=[]
        for editor_id, preferences in queriedForm.editors.items():
            if preferences["notification"]["newEntry"]:
                user=User.find(id=editor_id)
                if user and user.enabled:
                    emails.append(user.email)
        if emails:
            def sendEntryNotification():
                data=[]
                for field in queriedForm.getFieldIndexForDataDisplay():
                    if field['name'] in entry:
                        if field['name']=="marked":
                            continue
                        data.append( (field['label'], entry[field['name']]) )
                EmailServer().sendNewFormEntryNotification(emails, data, queriedForm.slug)
            thread = Thread(target=sendEntryNotification())
            thread.start()
        return render_template('thankyou.html', form=queriedForm, navbar=False)
    return render_template('view-form.html', form=queriedForm, navbar=False, no_bot=True)
