#!/usr/bin/env python3
# © 2025 TechnoLibre (http://www.technolibre.ca)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl)

import random
from datetime import datetime
from pprint import pprint

import asana
from asana.rest import ApiException

from odoo import _, api, fields, models


class AsanaSession(models.Model):
    _name = "asana.session"
    _description = "asana_session"

    name = fields.Char()

    api_token = fields.Char(help="API token to use Asana")

    api_token_responsable = fields.Char(
        help="API responsable users of api_token"
    )

    production_enabled = fields.Boolean(default=False)

    workspace_name = fields.Char(help="The workspace name.")

    workspace_gid = fields.Char(
        help="The workspace number identity to works with."
    )

    def get_task_information(self, task_gid):
        for rec in self:
            configuration = asana.Configuration()
            configuration.access_token = rec.api_token
            api_client = asana.ApiClient(configuration)

            # create an instance of the API class
            tasks_api_instance = asana.TasksApi(api_client)
            # task_gid = "321654"  # str | The task to operate on.
            opts = {
                "opt_fields": "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.default_access_level,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.id_prefix,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.privacy_setting,custom_fields.representation_type,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,custom_type,custom_type.name,custom_type_status_option,custom_type_status_option.name,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,parent,parent.created_by,parent.name,parent.resource_subtype,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,workspace,workspace.name",
                # list[str] | This endpoint returns a resource which excludes some properties by default. To include those optional properties, set this query parameter to a comma-separated list of the properties you wish to include.
            }

            try:
                # Get a task
                api_response = tasks_api_instance.get_task(task_gid, opts)
                # pprint(api_response)
                return api_response
            except ApiException as e:
                print("Exception when calling TasksApi->get_task: %s\n" % e)

    def action_test_asana(self):
        for rec in self:
            configuration = asana.Configuration()
            configuration.access_token = rec.api_token
            api_client = asana.ApiClient(configuration)

            user_gid = rec._print_user_information(api_client)
            dct_project_gid = rec._print_projects(api_client)
            dct_section_gid = rec._print_multiple_section(
                api_client, dct_project_gid
            )
            dct_task_assigne = rec._print_multiple_task_by_assignee(
                api_client, user_gid
            )
            dct_task_gid = rec._print_multiple_task_by_section(
                api_client, dct_section_gid
            )

            now = datetime.now()
            time_now = now.strftime("%Y-%m-%d %H:%M:%S")
            rec._update_task(
                api_client,
                dct_task_assigne,
                f"coucou Robot{random.randint(5,10)} - {time_now}",
            )
            print("end")

    def _print_projects(self, api_client):
        dct_project_gid = {}
        for rec in self:
            # create an instance of the API class
            projects_api_instance = asana.ProjectsApi(api_client)
            opts = {
                "limit": 50,
                # 'offset': "eyJ0eXAiOJiKV1iQLCJhbGciOiJIUzI1NiJ9",
                # 'assignee': "14641",
                # 'project': "321654",
                # 'section': "321654",
                "workspace": rec.workspace_gid,
                # 'completed_since': '2012-02-22T02:06:58.158Z',
                # 'modified_since': '2012-02-22T02:06:58.158Z',
                # 'opt_fields': "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,offset,parent,parent.created_by,parent.name,parent.resource_subtype,path,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,uri,workspace,workspace.name"
            }

            try:
                # Get multiple projects
                api_response = projects_api_instance.get_projects(opts)
                for data in api_response:
                    pprint(data)
                    dct_project_gid[data.get("gid")] = data
            except ApiException as e:
                print(
                    "Exception when calling ProjectsApi->get_projects: %s\n"
                    % e
                )
        return dct_project_gid

    def _print_multiple_section(self, api_client, dct_project_gid):
        dct_section_gid = {}
        for rec in self:
            for project_gid in dct_project_gid.keys():
                # create an instance of the API class
                sections_api_instance = asana.SectionsApi(api_client)
                opts = {
                    # 'limit': 50,
                    # 'offset': "eyJ0eXAiOJiKV1iQLCJhbGciOiJIUzI1NiJ9",
                    # 'assignee': "14641",
                    # 'project': project_gid,
                    # 'section': "321654",
                    # 'workspace': rec.workspace_gid,
                    # 'completed_since': '2012-02-22T02:06:58.158Z',
                    # 'modified_since': '2012-02-22T02:06:58.158Z',
                    # 'opt_fields': "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,offset,parent,parent.created_by,parent.name,parent.resource_subtype,path,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,uri,workspace,workspace.name"
                }

                try:
                    # Get multiple tasks
                    api_response = (
                        sections_api_instance.get_sections_for_project(
                            project_gid, opts
                        )
                    )
                    for data in api_response:
                        pprint(data)
                        dct_section_gid[data.get("gid")] = {
                            "project_gid": project_gid,
                            "data": data,
                        }
                except ApiException as e:
                    print(
                        "Exception when calling TasksApi->get_tasks: %s\n" % e
                    )
        return dct_section_gid

    def _print_multiple_task_by_assignee(self, api_client, user_gid):
        dct_task_gid = {}
        for rec in self:
            # create an instance of the API class
            tasks_api_instance = asana.TasksApi(api_client)
            opts = {
                "limit": 50,
                # 'offset': "eyJ0eXAiOJiKV1iQLCJhbGciOiJIUzI1NiJ9",
                "assignee": user_gid,
                # "assignee": "",
                # 'project': project_gid,
                # 'section': section_gid,
                "workspace": rec.workspace_gid,
                # 'completed_since': '2012-02-22T02:06:58.158Z',
                # 'modified_since': '2012-02-22T02:06:58.158Z',
                "opt_fields": "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.default_access_level,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.id_prefix,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.privacy_setting,custom_fields.representation_type,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,custom_type,custom_type.name,custom_type_status_option,custom_type_status_option.name,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,offset,parent,parent.created_by,parent.name,parent.resource_subtype,path,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,uri,workspace,workspace.name",
            }

            try:
                # Get multiple tasks
                api_response = tasks_api_instance.get_tasks(opts)
                for data in api_response:
                    pprint(data)
                    dct_task_gid[data.get("gid")] = data
            except ApiException as e:
                print("Exception when calling TasksApi->get_tasks: %s\n" % e)
        return dct_task_gid

    def _print_multiple_task_by_section(self, api_client, dct_section_gid):
        dct_task_gid = {}
        for rec in self:
            for section_gid, data in dct_section_gid.items():
                project_gid = data.get("project_gid")
                # create an instance of the API class
                tasks_api_instance = asana.TasksApi(api_client)
                opts = {
                    "limit": 50,
                    # 'offset': "eyJ0eXAiOJiKV1iQLCJhbGciOiJIUzI1NiJ9",
                    # "assignee": "",
                    "project": project_gid,
                    # 'section': section_gid,
                    # "workspace": rec.workspace_gid,
                    # 'completed_since': '2012-02-22T02:06:58.158Z',
                    # 'modified_since': '2012-02-22T02:06:58.158Z',
                    "opt_fields": "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.default_access_level,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.id_prefix,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.privacy_setting,custom_fields.representation_type,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,custom_type,custom_type.name,custom_type_status_option,custom_type_status_option.name,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,offset,parent,parent.created_by,parent.name,parent.resource_subtype,path,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,uri,workspace,workspace.name",
                }

                try:
                    # Get multiple tasks
                    api_response = tasks_api_instance.get_tasks(opts)
                    for data in api_response:
                        pprint(data)
                        dct_task_gid[data.get("gid")] = data
                except ApiException as e:
                    print(
                        "Exception when calling TasksApi->get_tasks: %s\n" % e
                    )
        return dct_task_gid

    def _update_task(self, api_client, dct_task, new_value):
        for rec in self:
            for task_gid, data in dct_task.items():
                project_gid = data.get("project_gid")
                # create an instance of the API class
                tasks_api_instance = asana.TasksApi(api_client)
                opts = {
                    # "limit": 50,
                    # # 'offset': "eyJ0eXAiOJiKV1iQLCJhbGciOiJIUzI1NiJ9",
                    # # "assignee": "",
                    # "project": project_gid,
                    # # 'section': section_gid,
                    # # "workspace": rec.workspace_gid,
                    # # 'completed_since': '2012-02-22T02:06:58.158Z',
                    # # 'modified_since': '2012-02-22T02:06:58.158Z',
                    # "opt_fields": "actual_time_minutes,approval_status,assignee,assignee.name,assignee_section,assignee_section.name,assignee_status,completed,completed_at,completed_by,completed_by.name,created_at,created_by,custom_fields,custom_fields.asana_created_field,custom_fields.created_by,custom_fields.created_by.name,custom_fields.currency_code,custom_fields.custom_label,custom_fields.custom_label_position,custom_fields.date_value,custom_fields.date_value.date,custom_fields.date_value.date_time,custom_fields.default_access_level,custom_fields.description,custom_fields.display_value,custom_fields.enabled,custom_fields.enum_options,custom_fields.enum_options.color,custom_fields.enum_options.enabled,custom_fields.enum_options.name,custom_fields.enum_value,custom_fields.enum_value.color,custom_fields.enum_value.enabled,custom_fields.enum_value.name,custom_fields.format,custom_fields.has_notifications_enabled,custom_fields.id_prefix,custom_fields.is_formula_field,custom_fields.is_global_to_workspace,custom_fields.is_value_read_only,custom_fields.multi_enum_values,custom_fields.multi_enum_values.color,custom_fields.multi_enum_values.enabled,custom_fields.multi_enum_values.name,custom_fields.name,custom_fields.number_value,custom_fields.people_value,custom_fields.people_value.name,custom_fields.precision,custom_fields.privacy_setting,custom_fields.representation_type,custom_fields.resource_subtype,custom_fields.text_value,custom_fields.type,custom_type,custom_type.name,custom_type_status_option,custom_type_status_option.name,dependencies,dependents,due_at,due_on,external,external.data,followers,followers.name,hearted,hearts,hearts.user,hearts.user.name,html_notes,is_rendered_as_separator,liked,likes,likes.user,likes.user.name,memberships,memberships.project,memberships.project.name,memberships.section,memberships.section.name,modified_at,name,notes,num_hearts,num_likes,num_subtasks,offset,parent,parent.created_by,parent.name,parent.resource_subtype,path,permalink_url,projects,projects.name,resource_subtype,start_at,start_on,tags,tags.name,uri,workspace,workspace.name",
                    "opt_fields": "name,notes",
                }

                body = {"data": {"notes": new_value}}

                try:
                    # Get multiple tasks
                    api_response = tasks_api_instance.update_task(
                        body, task_gid, opts
                    )
                    pprint(api_response)
                except ApiException as e:
                    print(
                        "Exception when calling TasksApi->get_tasks: %s\n" % e
                    )

    def _print_user_information(self, api_client):
        return_user_gid = ""
        for rec in self:
            # create an instance of the API class
            users_api_instance = asana.UsersApi(api_client)
            user_gid = "me"
            opts = {}

            try:
                # Get a user
                user = users_api_instance.get_user(user_gid, opts)
                pprint(user)
                return_user_gid = user.get("gid")
            except ApiException as e:
                print("Exception when calling UsersApi->get_user: %s\n")
        return return_user_gid
