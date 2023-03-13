# -*- encoding: UTF-8 -*-

""" pypdftk by revolunet

Authors: https://github.com/revolunet
See https://github.com/revolunet/pypdftk

Python module to drive the awesome pdftk binary.
See http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/

"""

import logging
import os
import subprocess
import tempfile
import shutil

log = logging.getLogger(__name__)

if os.getenv("PDFTK_PATH"):
    PDFTK_PATH = os.getenv("PDFTK_PATH")
else:
    PDFTK_PATH = "/usr/bin/pdftk"
    if not os.path.isfile(PDFTK_PATH):
        PDFTK_PATH = "pdftk"


def check_output(*popenargs, **kwargs):
    if "stdout" in kwargs:
        raise ValueError("stdout argument not allowed, it will be overridden.")
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output


def run_command(command, shell=False):
    """run a system command and yield output"""
    p = check_output(command, shell=shell)
    return p.split("\n")


try:
    run_command([PDFTK_PATH])
except OSError:
    logging.warning("pdftk test call failed (PDFTK_PATH=%r).", PDFTK_PATH)


def get_num_pages(pdf_path):
    """return number of pages in a given PDF file"""
    for line in run_command([PDFTK_PATH, pdf_path, "dump_data"]):
        if line.lower().startswith("numberofpages"):
            return int(line.split(":")[1])
    return 0


def fill_form(pdf_path, datas={}, out_file=None, flatten=True):
    """
    Fills a PDF form with given dict input data.
    Return temp file if no out_file provided.
    """
    cleanOnFail = False
    tmp_fdf = gen_xfdf(datas)
    handle = None
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()

    cmd = "%s %s fill_form %s output %s" % (PDFTK_PATH, pdf_path, tmp_fdf, out_file)
    if flatten:
        cmd += " flatten"
    try:
        run_command(cmd, True)
    except Exception:
        if cleanOnFail:
            os.remove(tmp_fdf)
        raise
    finally:
        if handle:
            os.close(handle)
    return out_file


def concat(files, out_file=None):
    """
    Merge multiples PDF files.
    Return temp file if no out_file provided.
    """
    cleanOnFail = False
    if not out_file:
        cleanOnFail = True
        handle, out_file = tempfile.mkstemp()
    if len(files) == 1:
        shutil.copyfile(files[0], out_file)
    args = [PDFTK_PATH]
    args += files
    args += ["cat", "output", out_file]
    try:
        run_command(args)
    except Exception:
        if cleanOnFail:
            os.remove(out_file)
        raise
    return out_file


def split(pdf_path, out_dir=None):
    """
    Split a single PDF file into pages.
    Use a temp directory if no out_dir provided.
    """
    cleanOnFail = False
    if not out_dir:
        cleanOnFail = True
        out_dir = tempfile.mkdtemp()
    out_pattern = "%s/page_%%02d.pdf" % out_dir
    try:
        run_command((PDFTK_PATH, pdf_path, "burst", "output", out_pattern))
    except Exception:
        if cleanOnFail:
            shutil.rmtree(out_dir)
        raise
    out_files = os.listdir(out_dir)
    out_files.sort()
    return [os.path.join(out_dir, filename) for filename in out_files]


def gen_xfdf(datas={}):
    """
    Generates a temp XFDF file suited for fill_form function, based on dict input data
    """
    fields = []
    for key, value in datas.items():
        fields.append(u"""<field name="%s"><value>%s</value></field>""" % (key, value))
    tpl = u"""<?xml version="1.0" encoding="UTF-8"?>
    <xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
        <fields>
            %s
        </fields>
    </xfdf>""" % "\n".join(
        fields
    )
    handle, out_file = tempfile.mkstemp()
    f = open(out_file, "w")
    f.write(tpl.encode("UTF-8"))
    f.close()
    return out_file


def replace_page(pdf_path, page_number, pdf_to_insert_path):
    """
    Replace a page in a PDF (pdf_path) by the PDF pointed by pdf_to_insert_path.
    page_number is the number of the page in pdf_path to be replaced. It is 1-based.
    """
    A = "A=" + pdf_path
    B = "B=" + pdf_to_insert_path
    lower_bound = "A1-" + str(page_number - 1)
    upper_bound = "A" + str(page_number + 1) + "-end"
    output_temp = tempfile.mktemp(suffix=".pdf")
    args = (PDFTK_PATH, A, B, "cat", lower_bound, "B", upper_bound, "output", output_temp)
    run_command(args)
    shutil.copy(output_temp, pdf_path)
    os.remove(output_temp)


def add_custom(custom, input_, output_):
    """
    Replace a page in a PDF (pdf_path) by the PDF pointed by pdf_to_insert_path.
    page_number is the number of the page in pdf_path to be replaced. It is 1-based.
    """
    A = "A=" + custom
    B = "B=" + input_
    output_temp = tempfile.mktemp(suffix=".pdf")
    args = (PDFTK_PATH, A, B, "cat", "A1", "B2-end", "output", output_temp)
    run_command(args)
    shutil.copy(output_temp, output_)
    os.remove(output_temp)


def stamp(pdf_path, stamp_pdf_path, output_pdf_path=None):
    """
    Applies a stamp (from stamp_pdf_path) to the PDF file in pdf_path.
    Useful for watermark purposes.
    If not output_pdf_path is provided, it returns a temporary file with the result PDF.
    """
    output = output_pdf_path or tempfile.mktemp(suffix=".pdf")
    args = [PDFTK_PATH, pdf_path, "multistamp", stamp_pdf_path, "output", output]
    run_command(args)
    return output


def update_metadata(pdf_path, metadata_path, output_pdf_path):
    args = [PDFTK_PATH, pdf_path, "update_info", metadata_path, "output", output_pdf_path]
    run_command(args)
