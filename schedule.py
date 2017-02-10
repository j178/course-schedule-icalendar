import re
from io import BytesIO
from tesserocr import PyTessBaseAPI, PSM

import requests
from PIL import Image
from bs4 import BeautifulSoup


class Course:
    def __init__(self, name, teacher, classroom, weeks, weekday, section):
        # 名字相同的一门课可能出现多次
        self.name = name
        self.teacher = teacher
        self.classroom = classroom
        self.weeks = weeks  # 上课的周目
        self.weekday = weekday  # 周几上课
        self.section = section  # 哪一节的课

    def __str__(self):
        return '{} {} {} [{}] {} {}'.format(self.name, self.teacher or '%', self.classroom,
                                            ','.join(str(e) for e in self.weeks),
                                            self.weekday,
                                            self.section)


class User:
    def __init__(self, username, password):
        self._session = requests.session()
        self.captcha_url = 'http://202.118.31.197/ACTIONVALIDATERANDOMPICTURE.APPPROCESS'
        self.login_url = 'http://202.118.31.197/ACTIONLOGON.APPPROCESS?mode='
        self.schedule_url = 'http://202.118.31.197/ACTIONQUERYSTUDENTSCHEDULEBYSELF.APPPROCESS'
        self.username = username
        self.password = password
        self._schedules = []

    @property
    def schedules(self):
        """获取课程表"""
        if not self._login():
            return None
        html = self._get_latest_schedules()

        self._parse_schedules(html)

        return self._schedules

    def _parse_schedules(self, raw):
        REGEX = re.compile(r'(.+?)&(?:(\D+?)&)?(.+?)&(.*?)周.*?节&?')

        def find_row(e):
            if e.name == 'tr':
                tds = e.find_all('td')
                if len(tds) >= 8:
                    brs = tds[0].find_all('br')
                    return len(brs) >= 2

        def parse_weeks(text):
            if text.isdigit():
                return int(text)

            r = re.compile(r'^(\d+)-(\d+)$')
            match = r.search(text)
            if match:
                start = int(match.group(1))
                end = int(match.group(2))
                return list(range(start, end + 1))

            weeks = []
            for w in text.split('.'):
                if w.isdigit():
                    weeks.append(int(w))
                elif '-' in w:
                    match = r.search(w)
                    if match:
                        start = int(match.group(1))
                        end = int(match.group(2))
                        weeks.extend(list(range(start, end + 1)))
            return weeks

        soup = BeautifulSoup(raw, 'lxml')
        table = soup.find('table', frame='box')
        # 找出一天各个时间段对应的tr
        rows = table.find_all(find_row, recursive=False)
        for section, row in enumerate(rows, start=1):
            # 找出一周中的每天的某一时间段的所有课程
            tds = row.find_all('td')[1:]
            for weekday, td in enumerate(tds, start=1):
                # 这个时间段有课
                brs = td.find_all('br')
                if len(brs) >= 3:
                    text = td.get_text('&')

                    for g in REGEX.findall(text):
                        name, teacher, classroom, week_text = g
                        weeks = parse_weeks(week_text)
                        course = Course(name, teacher, classroom, weeks, weekday, section)

                        self._schedules.append(course)

    def _get_latest_schedules(self):
        r = self._session.get(self.schedule_url)
        soup = BeautifulSoup(r.text, 'lxml')
        select_element = soup.find('select', {'name': 'YearTermNO'})
        last_option = select_element.contents[-1]
        # 当前课表即是最新的
        if last_option.has_attr('selected'):
            return r.text

        term_no = select_element.contents[-1]['value']
        r = self._session.post(self.schedule_url, {'YearTermNO': term_no})
        return r.text

    def _login(self):
        """登录教务处"""
        imagedata = self._get_captcha()
        captcha = self._recognize_captcha(imagedata)

        data = {
            "WebUserNO": self.username,
            "Password" : self.password,
            "Agnomen"  : captcha,
        }
        r = self._session.post(self.login_url, data)
        if 'TopFrame.jsp?UserType=BASE_STUDENT' in r.text:
            return True
        else:
            return False

    def _get_captcha(self):
        r = self._session.get(self.captcha_url)
        if r.status_code == 200:
            return r.content

    @staticmethod
    def _recognize_captcha(imagedata):
        """识别验证码"""
        REGEX = re.compile(r'(\d+)\s*([*+])\s*(\d+)')

        with PyTessBaseAPI() as ocr:
            ocr.SetPageSegMode(PSM.SINGLE_LINE)
            ocr.SetVariable('tessedit_char_whitelist', '0123456789+*=')
            image = Image.open(BytesIO(imagedata))
            ocr.SetImage(image)

            question = ocr.GetUTF8Text().strip()
            match = REGEX.search(question)
            answer = 0
            if match:
                if match.group(2) == '+':
                    answer = int(match.group(1)) + int(match.group(3))
                elif match.group(2) == '*':
                    answer = int(match.group(1)) * int(match.group(3))
                return answer
