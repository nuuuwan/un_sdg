import re

import xlsxwriter
from utils import filex, jsonx

from un_sdg._utils import log

REGEX_L1 = r'^Goal (?P<goal_num>\d{1,2})\.\s(?P<goal_description>.+)'
REGEX_L2 = r'^(?P<goal_num>\d{1,2}\.\w{1})\s(?P<goal_description>.+)'
REGEX_L3 = r'^(?P<goal_num>\d{1,2}\.\w{1}\.\d{1})\s(?P<goal_description>.+)'
REGEX_INDICATOR = r'C\w{6}'

DATA_INDEX_FILE = 'src/un_sdg/data/data_index.json'


L1_GOAL_NUM_TO_SHORT = {
    '1': 'poverty',
    '2': 'hunger',
    '3': 'health',
    '4': 'education',
    '5': 'gender',
    '6': 'water-sanit',
    '7': 'energy',
    '8': 'economy',
    '9': 'infrastructure',
    '10': 'inequality',
    '11': 'cities',
    '12': 'consumption',
    '13': 'climate',
    '14': 'oceans',
    '15': 'forrests',
    '16': 'peace',
    '17': 'partnership',
}


def load_raw():
    raw_file = 'src/un_sdg/data/raw.txt'
    log.info(f'Reading {raw_file}...')
    contents = filex.read(raw_file)
    lines = contents.split('\n')

    l1_goals = {}
    l2_goals = {}
    l3_goals = {}
    latest_l3_goal_num = None
    for line in lines[1:]:
        line = line.replace('[edit]', '')
        cells = line.split('\t')
        for cell in cells:
            result = re.search(REGEX_L1, cell)
            if result:
                result_data = result.groupdict()
                goal_num = result_data['goal_num']
                goal_description = result_data['goal_description']
                l1_goals[goal_num] = dict(
                    goal_num=goal_num,
                    goal_description=goal_description,
                    child_l2_goals={},
                )
                continue

            result = re.search(REGEX_L2, cell)
            if result:
                result_data = result.groupdict()
                goal_num = result_data['goal_num']
                goal_description = result_data['goal_description']
                l2_goals[goal_num] = dict(
                    goal_num=goal_num,
                    goal_description=goal_description,
                    child_l3_goals={},
                )
                continue

            result = re.search(REGEX_L3, cell)
            if result:
                result_data = result.groupdict()
                goal_num = result_data['goal_num']
                goal_description = result_data['goal_description']
                l3_goals[goal_num] = dict(
                    goal_num=goal_num,
                    goal_description=goal_description,
                )
                latest_l3_goal_num = goal_num
                continue

            result = re.search(REGEX_INDICATOR, cell)
            if result:
                l3_goals[latest_l3_goal_num]['unsd_indicator_code'] = cell
                continue

    for l2_goal_num, l2_goal in l2_goals.items():
        l1_goal_num = '.'.join(l2_goal_num.split('.')[:-1])
        l1_goals[l1_goal_num]['child_l2_goals'][l2_goal_num] = l2_goal

    for l3_goal_num, l3_goal in l3_goals.items():
        l2_goal_num = '.'.join(l3_goal_num.split('.')[:-1])
        l2_goals[l2_goal_num]['child_l3_goals'][l3_goal_num] = l3_goal

    jsonx.write(DATA_INDEX_FILE, l1_goals)
    log.info(f'Wrote data index to {DATA_INDEX_FILE}')

    return l1_goals


def load():
    return jsonx.read(DATA_INDEX_FILE)


def build_line(cells):
    return '\t'.join(
        list(map(str, cells)),
    )


def build_spreadsheet():
    data_index = load()
    spreadsheet_file = 'src/un_sdg/data/un_sdg.xlsx'
    workbook = xlsxwriter.Workbook(spreadsheet_file)
    _generic = {
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'font_name': 'Lato',
    }
    _l1 = workbook.add_format(
        _generic | {'bold': True, 'font_size': 18, 'font_color': '#c0c0c0'}
    )
    _l2 = workbook.add_format(
        _generic | {'bold': True, 'font_size': 12, 'font_color': '#808080'}
    )
    _l3 = workbook.add_format(
        _generic
        | {
            'bold': False,
            'font_size': 12,
            'font_color': '#000000',
            'bg_color': '#F0F8FF',
            'border': True,
            'border_color': '#c0c0c0',
        }
    )

    for l1_goal_num, l1_goal in data_index.items():
        short_name = L1_GOAL_NUM_TO_SHORT.get(l1_goal_num, '')
        worksheet_label = f'{l1_goal_num}-{short_name}'
        worksheet = workbook.add_worksheet(worksheet_label)

        for i_col in range(1, 20, 2):
            worksheet.set_column(i_col, i_col, 6)
            worksheet.set_column(i_col + 1, i_col + 1, 48)

        i_row = 0
        i_col = 1
        worksheet.write(i_row, i_col, l1_goal_num, _l1)
        i_col += 1
        worksheet.write(i_row, i_col, l1_goal['goal_description'], _l1)

        for l2_goal_num, l2_goal in l1_goal['child_l2_goals'].items():

            i_row += 1
            i_col = 1
            worksheet.write(i_row, i_col, l2_goal_num, _l2)
            i_col += 1
            worksheet.write(i_row, i_col, l2_goal['goal_description'], _l2)
            i_col += 1

            for l3_goal_num, l3_goal in l2_goal['child_l3_goals'].items():
                worksheet.write(i_row, i_col, l3_goal_num, _l3)
                i_col += 1
                worksheet.write(i_row, i_col, l3_goal['goal_description'], _l3)
                i_col += 1

    workbook.close()
    log.info(f'Wrote spreadsheet to {spreadsheet_file}')


if __name__ == '__main__':
    load_raw()
    build_spreadsheet()
