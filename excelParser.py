#coding=utf-8
import os
import sys
import re
import urllib2
import xlrd

blankRow_patt = re.compile('^(<td></td>)*$')
MAX_ROWS = 25

class excelParser(object):
    def __init__(self, content):
        wb = xlrd.open_workbook(file_contents=content, on_demand=True, formatting_info=True, ragged_rows=True)
        sheet = wb.sheet_by_index(0)

        merged_spans = dict((((rlo, clo), (rhi-rlo, chi-clo)) for rlo, rhi, clo, chi in sheet.merged_cells))

        rows = []
        for row_idx in range(min(sheet.nrows, MAX_ROWS)):
            cols = []
            column = ''
            for col_idx in range(sheet.row_len(row_idx)):
                coord = (row_idx, col_idx)
                if sheet.cell(*coord).ctype == xlrd.XL_CELL_BLANK:
                    continue
                if coord in merged_spans:
                    col = '<td align="center" rowspan="%s" colspan="%s">%s</td>' % (merged_spans[coord][0], merged_spans[coord][1], sheet.cell_value(*coord))
                else:
                    col = '<td>%s</td>' % sheet.cell_value(*coord)
                cols.append(col)
            row = ''.join(cols)
            if not blankRow_patt.match(row):
                rows.append(row)
        html_tbl = '</tr><tr>'.join(rows)
        html_tbl = '<table style="border-collapse: collapse; border: solid 1px #999" border="1"><tr>' + html_tbl + '</tr></table>'
        if sheet.nrows > MAX_ROWS:
            last_tr = html_tbl.rfind('<tr>')
            html_tbl = html_tbl[:last_tr+3]+' style=" border-bottom: dashed #777;"'+html_tbl[last_tr+3:]
        self.content = html_tbl


    def getMainContent(self):
        return self.content

    def getTitlePrefix(self):
        return '[XLS]'

if __name__=='__main__':
    fname = 'namesdemo.xls'
    fname = '30363.xls'
    # fname = 'index (1).xls'
    xlin = urllib2.urlopen('http://www2.dhu.edu.cn/dhuxxxt/upload/newstxt/anshunbm.xls').read()
    # xlin = open(fname, 'rb').read()
    print excelParser(xlin).getMainContent().encode('utf-8')
