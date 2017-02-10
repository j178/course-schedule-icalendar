import re


def test_login():
    from schedule import User
    user = User('20144994', 'dengqiaoyi321jiayou')
    print('\n'.join(str(s) for s in user.schedules))


REGEX = re.compile(r'(.+?)&(?:(.+?)&)?(.+?)&(.*?周).*?节&?')


def parse():
    from bs4 import BeautifulSoup, NavigableString

    def find_row(e):
        if e.name == 'tr':
            tds = e.find_all('td')
            if len(tds) >= 8:
                brs = tds[0].find_all('br')
                return len(brs) >= 2

    def parse_weeks(text):
        match = re.search(r'(\d+)(?:-(\d+))?', text)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else None
            return list(range(start, end + 1))
        if '单周' in text or '双周' in text:
            weeks = re.findall(r'((\d+)\.?)+', text)
            return [int(week) for week in weeks]

    with open('sche.html') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
        table = soup.find('table', frame='box')
        # 找出一天六节课的tr
        rows = table.find_all(find_row, recursive=False)
        for section, row in enumerate(rows, start=1):
            tds = row.find_all('td')[1:]
            for weekday, td in enumerate(tds, start=1):
                # 这个空格有课
                brs = td.find_all('br')
                if len(brs) >= 3:
                    text = td.get_text('&')

                    for g in REGEX.findall(text):
                        name, teacher, classroom, week_text = g
                        weeks = parse_weeks(week_text)

                        print(name, teacher, classroom, weeks, weekday, section)
                        # course = Course(name, teacher, classroom, weeks, weekday, section)
                        #
                        # self._schedules.append(course)


if __name__ == '__main__':
    test_login()
    # parse()
