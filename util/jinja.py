import os
from typing import Union, Dict, Any, Set

import logging

LOG = logging.getLogger(__name__)

try:
    from . import data
except ImportError as import_err:
    LOG.error(f"Unable to import module: {import_err}")
    raise import_err

try:
    import jinja2.exceptions
    from jinja2 import Environment, FileSystemLoader, Template, DebugUndefined
    from jinja2.meta import find_undeclared_variables
except ImportError as import_err:
    LOG.error(f"Jinja2 is a required package: Please install it. {import_err}")
    raise import_err


class Jinja:
    """
    Class for rendering Jinja templates
    """

    def __init__(self):
        pass

    @staticmethod
    def render_template_from_file(template_file: str,
                                  fail_on_undefined: bool = True,
                                  **variables: Union[str, Dict[str, Any]]) -> str:
        """
        Renders template from supplied file using Jinja2
        :param template_file: source file to read from
        :param fail_on_undefined: whether to fail if encountering undefined variable or skip undefined
        :param variables: variables to be used to template. Accepts a dict, a dict subclass or some keyword arguments
                          knights='that say nih'
                         {'knights': 'that say nih'}
        :return: rendered template as string object
        """

        # TODO Assumption is given absolute path to file. Need to test various ways of being passed
        base_path: str = template_file.rsplit(os.sep, 1)[0] + os.sep
        file_name: str = template_file.rsplit(os.sep)[-1]

        file_loader: jinja2.FileSystemLoader = FileSystemLoader(searchpath=base_path)

        env: jinja2.environment = Environment(loader=file_loader, autoescape=True, undefined=DebugUndefined)

        template: jinja2.environment.Template = env.get_template(file_name)
        rendered_template: str = template.render(**variables)

        try:
            abstract = env.parse(rendered_template)
            undefined: Set[str] = find_undeclared_variables(abstract)

            if undefined:
                raise jinja2.exceptions.UndefinedError(
                    f'Undefined variables when rendering template {base_path}{file_name}: {undefined}')
        except jinja2.exceptions.UndefinedError as jinja_err:
            if fail_on_undefined:
                raise jinja_err
            else:
                LOG.warning(jinja_err)

        return rendered_template

    @staticmethod
    def write_template_file(template_file: str,
                            render_variables: Dict[str, str],
                            destination_file: str = None,
                            fail_on_undefined: bool = True,
                            backup_original: bool = True,
                            modification_message: str = "") -> str:
        """
        Helper method to render jinja templates from file. Renders file and optionally backs up original if it exists
        :param modification_message: Message to append to beginning of rendered file
        :param render_variables: variables to be used in rendering
        :param destination_file: Destination file to write rendered template to. Defaults to origin path without .j2
        :param template_file: src file to be rendered
        :param fail_on_undefined: if encountered undefined variable, fail, or skip undefined
        :param backup_original: Make copy of file before overwriting
        :return: Location of rendered file on success
        """

        try:
            rendered: str = Jinja.render_template_from_file(**render_variables,
                                                            template_file=template_file,
                                                            fail_on_undefined=fail_on_undefined)

        except (jinja2.exceptions.TemplateError, jinja2.exceptions.UndefinedError) as err:
            raise err

        if modification_message:
            rendered: str = '\n'.join([modification_message, rendered])

        try:
            if destination_file:
                rendered_file_path = destination_file
            else:
                # Default to same path as template file without the .j2 extension
                rendered_file_path = template_file.split('.j2')[0]

            if backup_original:
                data.backup_file(rendered_file_path)

            with open(rendered_file_path, "w+") as f:
                f.write(rendered)
        except OSError as err:
            ex_message = f"File Error: {err}"
            raise ex_message

        return rendered_file_path
