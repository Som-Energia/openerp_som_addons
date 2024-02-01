#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from mako.template import Template
import pdfkit
import pypdftk_ as pypdftk

ENCODING = "utf-8"
WKHTMLTOPDF = os.getenv("WKHTMLTOPDF_", None)


def read_mako_template(path):
    with open(path) as f:
        template = f.read()
    return template


def write_html(path, name, result):
    if not os.path.exists(path):
        os.makedirs(path)
    try:
        filename = os.path.join(path, name + ".html")
        with open(filename, "w") as f:
            f.write(result.encode(ENCODING))
    except Exception as e:
        raise Exception(
            """Report in html for  %s was not generated due to
                problems with write_html function. Error: %s"""
            % (name, e)
        )


def write_pdf(path, name):
    try:
        options = {
            "--margin-left": "3",  # default is 10 = 14 mm
            "--margin-right": "3",  # default is 10
            "--margin-top": "3",  # default is 10  42.9
            "--margin-bottom": "3",
            "--orientation": "portrait",
        }
        input_ = os.path.join(path, name + ".html")
        if not os.path.exists(input_):
            raise Exception("""Report in html %s not present""" % input_)
        output_ = os.path.join(path, name + ".pdf")
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF)
        pdfkit.from_file(input_, output_, options=options, configuration=config)
    except Exception as e:
        raise Exception(
            """Report in pdf for %s was not generated due to problems
                 in the write_pdf function. Error: %s"""
            % (path, e)
        )
    return output_


def _(message):
    return message.decode(ENCODING)


def add_custom(original_pdf, custom_pdf, output_pdf):
    output_pdf_aux = output_pdf + ".aux"
    pypdftk.stamp(original_pdf, custom_pdf, output_pdf_aux)
    num_pages = pypdftk.get_num_pages(original_pdf)
    if num_pages > 1:
        pypdftk.add_custom(output_pdf_aux, original_pdf, output_pdf)
        os.unlink(output_pdf_aux)
    else:
        os.rename(output_pdf_aux, output_pdf)


def customize(report, template_name, path_aux, path_output):
    fields = ["name", "surname", "address", "cups", "lang"]
    customer = {field: report[field] for field in fields}
    result = Template(read_mako_template(template_name), input_encoding=ENCODING).render(
        customer=customer, _=_
    )
    report_name = report["contract_name"]
    write_html(path_aux, report_name, result)
    custom_pdf = write_pdf(path_aux, report_name)
    original_pdf = report["report"]
    filename = os.path.basename(report["report"])
    output_pdf = os.path.join(path_output, filename)
    add_custom(original_pdf, custom_pdf, output_pdf)
    return output_pdf
