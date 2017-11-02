import logging
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range, xl_col_to_name
import models
import settings

logger = logging.getLogger(__name__)

key_ele_name = 'th'
total_ele_name = 'th'

class Cell(object):
    def __init__(self, content, row_span=1, col_span=1, cell_format=None, ele_name='td'):
        self.content = content
        self.col_span = col_span
        self.row_span = row_span
        self.cell_format = cell_format
        self.ele_name = ele_name

    def write2excel(self, worksheet, start_row, start_col, xlsx_format=None):
        xlsx_format = xlsx_format if xlsx_format else self.cell_format
        if self.row_span == 1 and self.col_span == 1:
            xlsx_cell = xl_rowcol_to_cell(start_row, start_col)
            worksheet.write(xlsx_cell, self.content, xlsx_format)
        else:
            xlsx_cell = xl_range(start_row, start_col, start_row + self.row_span - 1, start_col + self.col_span - 1)
            worksheet.merge_range(xlsx_cell, self.content, xlsx_format)

    def to_html(self, html_format=None):
        html_template = '<%s %s> %s </%s>'
        content = self.content
        if type(self.content) == int:
            content = format(content, ',')
        return html_template % (self.ele_name, self.get_attr_str(html_format),
                                content, self.ele_name)

    def get_attr_str(self, html_format):
        format = html_format if html_format else self.cell_format
        rowspan_css = 'rowspan="%s"' % self.row_span if self.row_span > 1 else ''
        colspan_css = 'colspan="%s"' % self.col_span if self.col_span > 1 else ''
        return ' '.join((rowspan_css, colspan_css, format)).strip()

    def __repr__(self):
        return str(self.content)


class Row(object):
    def __int__(self):
        self.cells = []

def get_obj_type(obj):
    if type(obj) is int:
        return 'int'
    elif type(obj) is float:
        return 'float'
    if type(obj) is str:
        return 'str'



def get_rowspan(leveled_data, total_keys=None):
    has_total_key = total_keys and ('level%s_total_key' % leveled_data.level in total_keys)
    total_row_count = 1 if has_total_key else 0

    if type(leveled_data) is models.Level2Dict:
        return leveled_data.get_size() + total_row_count  # add the total row
    else:
        return sum(get_rowspan(x, total_keys) for x in leveled_data.get_sub_data()) + total_row_count


def get_key_format(level_data, formats):
    if type(level_data) is models.Level2Dict:
        return formats.get('level2_key')
    elif type(level_data) is models.Level3Dict:
        return formats.get('level3_key')
    elif type(level_data) is models.Level4Dict:
        return formats.get('level4_key')


def _flat_level_data_total(level_data, metrics, total_keys, formats):
    key_key = 'level%s_total_key' % level_data.level
    if not total_keys or key_key not in total_keys:
        return None

    cells = []
    cells.append(Cell(total_keys.get(key_key),
                      col_span=level_data.level - 1,
                      cell_format=formats.get(key_key),
                      ele_name=total_ele_name))
    for metric in metrics:
        value = level_data.get_total().get(metric, 0)
        format_key = 'level%s_total_value_%s' % (level_data.level, get_obj_type(value))
        format_key2 = 'level%s_total_value' % (level_data.level,)
        value_format = formats.get(format_key, formats.get(format_key2, None))
        cells.append(Cell(level_data.get_total().get(metric, 0),
                          cell_format=value_format,
                          ele_name=total_ele_name))
    return cells


def _flat_level1_data(level_data, metrics, formats):
    """
    write a level1 data to a worksheet
    :param level_data: data to be write
    :param metrics: write metrics. if metric is not there, 0 is fill
    :return: Cells
    """
    # first: write key
    key_format = formats.get('level1_key')
    cells = [Cell(level_data.get_key(), cell_format=key_format, ele_name=key_ele_name), ]

    # secondly, write number for all metrics
    for metric in metrics:
        value = level_data.get_value(metric)
        format_key = 'level1_value_%s' % get_obj_type(value)
        value_format = formats.get(format_key, formats.get('level1_key'))
        cells.append(Cell(value, cell_format=value_format))

    return cells


def _flat_level2_data(level_data, metrics, total_keys, formats, sort_configs=None):
    """
    write a level2 data to a worksheet
    :param level_data: data to be write
    :param metrics: write metrics. if metric is not there, 0 is fill
    :return: Cell[[]]
    """
    cells_2d = []
    sort_config = sort_configs.get('level%s_data' % level_data.level, {}) if sort_configs else {}
    for row_index, level1_data in enumerate(level_data.get_sub_data(**sort_config)):
        # 1. write level2 key if is first row
        cells_row = _flat_level1_data(level1_data, metrics, formats)
        if row_index == 0:
            key_format = get_key_format(level_data, formats)
            row_span = get_rowspan(level_data, total_keys)
            key_element = Cell(content=level_data.get_key(),
                               row_span=row_span,
                               cell_format=key_format,
                               ele_name=key_ele_name)
            cells_row.insert(0, key_element)
        cells_2d.append(cells_row)

    # 3. write total for level1
    cells_1d = _flat_level_data_total(level_data, metrics, total_keys, formats)
    if cells_1d:
        cells_2d.append(cells_1d)
    return cells_2d


def flat_level_data(level_data, metrics, total_keys, formats, sort_configs=None):
    """
    write a level3 data to a worksheet
    :param level_data: data to be write
    :param metrics: write metrics. if metric is not there, 0 is fill
    :param total_keys: key for total col. should be a dict like：
     {'level3_total_key': '总计', 'level2_total_key': '小计', 'level1_total_key': 'Total'}
    :param formats formats for cell
    :param sort_by_metric weather to sort sub data by metrics[0]
    :return: writen row number
    """

    if type(level_data) is models.Level1Dict:
        return _flat_level1_data(level_data, metrics, formats)
    elif type(level_data) is models.Level2Dict:
        return _flat_level2_data(level_data, metrics, total_keys, formats, sort_configs)
    else:
        cells_2d = []
        sort_config = sort_configs.get('level%s_data' % level_data.level, {}) if sort_configs else {}

        for row_index, sub_level_data in enumerate(level_data.get_sub_data(**sort_config)):
            # 1. write level2 key if is first row
            cells_row = flat_level_data(sub_level_data, metrics, total_keys, formats, sort_configs)
            if row_index == 0:
                key_format = get_key_format(level_data, formats)
                row_span = get_rowspan(level_data, total_keys)
                logger.debug("%s rowspan: %s" % (level_data.get_key(), row_span))
                key_element = Cell(content=level_data.get_key(),
                                   row_span=row_span,
                                   cell_format=key_format,
                                   ele_name=key_ele_name)
                cells_row[0].insert(0, key_element)
            cells_2d.extend(cells_row)

        # 3. write total
        cells_1d = _flat_level_data_total(level_data, metrics, total_keys, formats)
        if cells_1d:
            cells_2d.append(cells_1d)
        return cells_2d


def get_keys(subtractor, minuend):
    all_keys = subtractor.sub_data.keys()
    for key in minuend.sub_data.keys():
        if key not in subtractor.sub_data:  # dict to improve performance
            all_keys.append(key)
    return all_keys


def _add_diff_metric2level1_data(target_data, leading_keys, subtractor, minuend, metric_map):
    for derived_metric, metric in metric_map.items():
        subtractor_value = subtractor.get_value(metric[0])
        minuend_value = minuend.get_value(metric[1]) if minuend else 0
        args = leading_keys + [derived_metric, subtractor_value - minuend_value]
        getattr(target_data, 'add_sub_data')(*args)


def _add_diff_metric2level_data(target_data, leading_keys, subtractor, minuend, metric_map):
    if type(subtractor) != type(minuend):
        raise Exception('typeof subtractor(%s) and minuend(%s) is different' % (type(subtractor), type(minuend)))
    if type(subtractor) is models.Level1Dict:
        _add_diff_metric2level1_data(target_data, leading_keys, subtractor, minuend, metric_map)
    else:
        for key1 in get_keys(subtractor, minuend):
            sub_substractor1 = subtractor.get_sub_data(key1)
            sub_minuend1 = minuend.get_sub_data(key1)
            new_leading_keys = leading_keys + [key1]
            _add_diff_metric2level_data(target_data, new_leading_keys, sub_substractor1, sub_minuend1, metric_map)
    return subtractor


def add_diff_metric2level_data(subtractor, minuend, metric_map):
    """
    add metric to subtractor base of metric map
    :param subtractor: subtractor value to get from, also metric to be add to
    :param minuend: minuend value to get from
    :param metric_map: example:
        incr_metrics_map = {
        'inOneDay_inactive': ('everLogin', 'everLogin_inOneDay'),
        }
        means subtractor.add_sub_data(keys?, 'inOneDay_inactive',
                                      subtractor.get_value('everLogin') - minuend.get_value('everLogin_inOneDay'))
    :return: subtractor
    """
    return _add_diff_metric2level_data(subtractor, [], subtractor, minuend, metric_map)
