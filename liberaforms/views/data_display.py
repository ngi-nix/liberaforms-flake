"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

from flask import Blueprint, request, jsonify
from flask_babel import gettext as _
from liberaforms.models.form import Form
#from liberaforms.models.formuser import FormUser
from liberaforms.models.answer import Answer
from liberaforms.models.schemas.form import FormSchemaForDataDisplay
from liberaforms.models.schemas.answer import AnswerSchema
from liberaforms.utils.wraps import *

from pprint import pprint

data_display_bp = Blueprint('data_display_bp', __name__)

default_forms_field_index = [
                {'name': 'form_name__html', 'label': _('Form name')},
                {'name': 'answers__html', 'label': _('Answers')},
                {'name': 'last_answer_date', 'label': _('Last answer')},
                {'name': 'is_public', 'label': _('Public')},
                {'name': 'is_shared', 'label': _('Shared')},
                {'name': 'created', 'label': _('Created')}
            ]

def get_forms_field_index(user):
    if 'forms_field_index' in user.preferences:
        return user.preferences['forms_field_index']
    else:
        return default_forms_field_index

def get_forms_order_ascending(user):
    if 'forms_order_ascending' in user.preferences:
        return user.preferences['forms_order_ascending']
    else:
        return True

def get_forms_order_by(user):
    if 'forms_order_by' in user.preferences:
        return user.preferences['forms_order_by']
    else:
        return 'created'

""" Forms """

@data_display_bp.route('/data-display/forms/<int:user_id>', methods=['GET'])
@enabled_user_required__json
def my_forms(user_id):
    """ Returns json required by Vue dataTable component.
        Hyperlinks to be rendered by the component and are declared by trailing '__html'
    """
    if not user_id == g.current_user.id:
        return jsonify("Denied"), 401
    forms = g.current_user.get_forms()
    form_count = forms.count()
    page = request.args.get('page', type=int)
    if page:
        print(f"page: {page}")
        forms = Form.find_all(editor_id=g.current_user.id).paginate(page, 10, False).items

    field_index = get_forms_field_index(g.current_user)
    items = []
    for form in FormSchemaForDataDisplay(many=True).dump(forms):
        item = {}
        data = {}
        id = form['id']
        slug = form['slug']
        data['form_name__html'] = {
            'value': slug,
            'html': f"<a href='/forms/view/{id}'>{slug}</a>"
        }
        total_answers = form['total_answers']
        stats_icon = f"<i class='fa fa-bar-chart' aria-label=\"{_('Statistics')}\"></i>"
        stats_url = f"<a href='/forms/answers/stats/{id}'>{stats_icon}</a>"
        count_url = f"<a href='/forms/answers/{id}' alt_text=\"{_('Answers')}\">{total_answers}</a>"
        data['answers__html'] = {
            'value': total_answers,
            'html': f"{stats_url} {count_url}"

        }
        for key in form.keys():
            if key == 'slug' or key == 'total_answers':
                continue
            if key == 'id':
                item[key] = form[key]
                continue;
            if key == 'created':
                item[key] = form[key]
                continue;
            data[key] = form[key]
        item['data'] = data
        #pprint(data)
        items.append(item)
        #pprint(items)

    return jsonify(
        items=items,
        meta={'total': form_count,
              'field_index': field_index,
              'order_by': get_forms_order_by(g.current_user),
              'ascending': get_forms_order_ascending(g.current_user),
              'editable_fields': False}
    ), 200

@data_display_bp.route('/data-display/forms/<int:user_id>/change-index', methods=['POST'])
@enabled_user_required__json
def change_forms_field_index(user_id):
    """ Changes Users' Form (all forms) field index preference
    """
    if not user_id == g.current_user.id:
        return jsonify("Forbidden"), 403
    data = request.get_json(silent=True)
    new_first_field_name = data['field_name']
    field_index = get_forms_field_index(g.current_user)
    field_to_move = None
    for field in field_index:
        if field['name'] == new_first_field_name:
            field_to_move = field
            break
    if field_to_move:
        old_index = field_index.index(field_to_move)
        field_index.insert(0, field_index.pop(old_index))
        g.current_user.preferences['forms_field_index'] = field_index
        g.current_user.save()
        return jsonify(
            {'field_index': g.current_user.preferences['forms_field_index']}
        ), 200
    return jsonify("Not Acceptable"), 406


@data_display_bp.route('/data-display/forms/<int:user_id>/reset-index', methods=['POST'])
@enabled_user_required__json
def reset_forms_field_index(user_id):
    """ Resets Users' Form field index preference
    """
    if not user_id == g.current_user.id:
        return jsonify("Forbidden"), 403
    g.current_user.preferences['forms_field_index'] = default_forms_field_index
    g.current_user.save()
    return jsonify(
        {'field_index': g.current_user.preferences['forms_field_index']}
    ), 200

@data_display_bp.route('/data-display/forms/<int:user_id>/order-by-field', methods=['POST'])
@enabled_user_required__json
def forms_order_by_field(user_id):
    """ Set User's forms order_by preference
    """
    if not user_id == g.current_user.id:
        return jsonify("Forbidden"), 403
    data = request.get_json(silent=True)
    if not 'order_by_field_name' in data:
        return jsonify("Not Acceptable"), 406
    field_names = [ field['name'] for field in default_forms_field_index ]
    if not data['order_by_field_name'] in field_names:
        return jsonify("Not Acceptable"), 406
    g.current_user.preferences['forms_order_by'] = data['order_by_field_name']
    g.current_user.save()
    return jsonify(
        {'order_by_field_name': g.current_user.preferences['forms_order_by']}
    ), 200

@data_display_bp.route('/data-display/forms/<int:user_id>/toggle-ascending', methods=['POST'])
@enabled_user_required__json
def forms_toggle_ascending(user_id):
    """ Toggle User's forms ascending order preference
    """
    if not user_id == g.current_user.id:
        return jsonify("Forbidden"), 403
    preference = get_forms_order_ascending(g.current_user)
    g.current_user.preferences['forms_order_ascending'] = False if preference else True
    g.current_user.save()
    return jsonify(
        {'ascending': g.current_user.preferences['forms_order_ascending']}
    ), 200


""" Answers """

@data_display_bp.route('/data-display/form/<int:form_id>/answers', methods=['GET'])
@enabled_user_required__json
def form_answers(form_id):
    """ Return json required by vue data-table component
    """
    form = g.current_user.get_form(form_id)
    if not form:
        return jsonify("Not found"), 404
    page = request.args.get('page', type=int)
    if page:
        print(f"page: {page}")
        answers = form.answers.paginate(page, 10, False).items
    else:
        answers = form.answers
    field_index = form.get_user_field_index_preference(g.current_user)
    return jsonify(
        items=AnswerSchema(many=True).dump(answers),
        meta={'total': form.answers.count(),
              'field_index': field_index,
              'ascending': form.get_answers_order_ascending(g.current_user),
              'editable_fields': False,
        }
    ), 200

@data_display_bp.route('/data-display/answer/<int:answer_id>/mark', methods=['POST'])
@enabled_user_required__json
def toggle_answer_mark(answer_id):
    answer = Answer.find(id=answer_id)
    if not answer:
        return jsonify("Not found"), 404
    if not g.current_user.get_form(answer.form.id):
        return jsonify("Forbidden"), 403
    answer.marked = False if answer.marked == True else True
    answer.save()
    return jsonify(marked=answer.marked), 200


@data_display_bp.route('/data-display/answer/<int:answer_id>/delete', methods=['DELETE'])
@enabled_user_required__json
def delete_answer(answer_id):
    answer = Answer.find(id=answer_id)
    if not answer:
        return jsonify("Not found"), 404
    form = g.current_user.get_form(answer.form.id, is_editor=True)
    if not form:
        return jsonify("Forbidden"), 403
    answer.delete()
    form.expired = form.has_expired()
    form.save()
    form.add_log(_("Deleted an answer"))
    return jsonify(deleted=True), 200


@data_display_bp.route('/data-display/form/<int:form_id>/answers/change-index', methods=['POST'])
@enabled_user_required__json
def change_answer_field_index(form_id):
    """ Changes User's Answer field index preference for this form
    """
    form = g.current_user.get_form(form_id)
    if not form:
        return jsonify("Not found"), 404
    field_index = form.get_user_field_index_preference(g.current_user.id)
    if not field_index:
        field_index = form.get_field_index_for_data_display()

    data = request.get_json(silent=True)
    new_first_field_name = data['field_name']
    field_to_move = None
    for field in field_index:
        if field['name'] == new_first_field_name:
            field_to_move = field
            break
    if field_to_move:
        old_index = field_index.index(field_to_move)
        field_index.insert(1, field_index.pop(old_index))
        form.save_user_field_index_preference(g.current_user, field_index)
        return jsonify(
            {'field_index': field_index}
        ), 200
    return jsonify("Not Acceptable"), 406


@data_display_bp.route('/data-display/form/<int:form_id>/answers/reset-index', methods=['POST'])
@enabled_user_required__json
def reset_answers_field_index(form_id):
    """ Resets User's Answer field index preference for this form
    """
    form = g.current_user.get_form(form_id)
    if not form:
        return jsonify("Not found"), 404
    field_index = form.get_field_index_for_data_display()
    form.save_user_field_index_preference(g.current_user, field_index)
    return jsonify(
        {'field_index': field_index}
    ), 200

@data_display_bp.route('/data-display/form/<int:form_id>/answers/toggle-ascending', methods=['POST'])
@enabled_user_required__json
def answers_toggle_ascending(form_id):
    """ Toggle user's asnwers ascending order preference
    """
    form = g.current_user.get_form(form_id)
    if not form:
        return jsonify("Not found"), 404
    return jsonify(
        {'ascending': form.toggle_user_answers_ascending_order(g.current_user)}
    ), 200
