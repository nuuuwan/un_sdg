import re

from utils import filex, jsonx

from un_sdg._utils import log

REGEX_L1 = r'^Goal (?P<goal_num>\d{1,2})\.\s(?P<goal_description>.+)'
REGEX_L2 = r'^(?P<goal_num>\d{1,2}\.\w{1})\s(?P<goal_description>.+)'
REGEX_L3 = r'^(?P<goal_num>\d{1,2}\.\w{1}\.\d{1})\s(?P<goal_description>.+)'
REGEX_INDICATOR = r'C\w{6}'


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
                    children={},
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
                    children={},
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
        l1_goals[l1_goal_num]['children'][l2_goal_num] = l2_goal

    for l3_goal_num, l3_goal in l3_goals.items():
        l2_goal_num = '.'.join(l3_goal_num.split('.')[:-1])
        l2_goals[l2_goal_num]['children'][l3_goal_num] = l3_goal

    data_index_file = 'src/un_sdg/data/data_index.json'
    jsonx.write(data_index_file, l1_goals)
    log.info(f'Wrote data index to {data_index_file}...')


if __name__ == '__main__':
    load_raw()
