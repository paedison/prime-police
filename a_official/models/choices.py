from datetime import datetime


def default_year():
    return datetime.now().year + 1


def year_choice() -> list:
    choice = [(year, f'{year}년') for year in range(2023, datetime.now().year + 2)]
    choice.reverse()
    return choice


def exam_choice() -> dict:
    return {'경위': '경위공채'}


def subject_choice() -> dict:
    return {
        '형사': '형사법', '헌법': '헌법',
        '경찰': '경찰학', '범죄': '범죄학',
        '민법': '민법총칙', '행법': '행정법', '행학': '행정학',
    }


def selection_choice() -> dict:
    return {'민법': '민법총칙', '행법': '행정법', '행학': '행정학'}


def subject_fields() -> dict:
    return {
        '형사': 'hyeongsa', '헌법': 'heonbeob', '경찰': 'gyeongchal', '범죄': 'beomjoe',
        '민법': 'minbeob', '행법': 'haengbeob', '행학': 'haenghag',
    }


def number_choice() -> list:
    return [(number, f'{number}번') for number in range(1, 41)]


def answer_choice() -> dict:
    return {
        1: '①', 2: '②', 3: '③', 4: '④',
        12: '①②', 13: '①③', 14: '①④', 23: '②③', 24: '②④', 34: '③④',
        123: '①②③', 124: '①②④', 134: '①③④', 234: '②③④',
        1234: '①②③④',
    }


def rating_choice() -> dict:
    return {1: '⭐️', 2: '⭐️⭐️', 3: '⭐️⭐️⭐️', 4: '⭐️⭐️⭐️⭐️', 5: '⭐️⭐️⭐️⭐️⭐️'}


def university_choice() -> list:
    return [
        ('강원대학교', '강원대학교'),
        ('건국대학교', '건국대학교'),
        ('경북대학교', '경북대학교'),
        ('경희대학교', '경희대학교'),
        ('고려대학교', '고려대학교'),
        ('동아대학교', '동아대학교'),
        ('부산대학교', '부산대학교'),
        ('서강대학교', '서강대학교'),
        ('서울대학교', '서울대학교'),
        ('서울시립대학교', '서울시립대학교'),
        ('성균관대학교', '성균관대학교'),
        ('아주대학교', '아주대학교'),
        ('연세대학교', '연세대학교'),
        ('영남대학교', '영남대학교'),
        ('원광대학교', '원광대학교'),
        ('이화여자대학교', '이화여자대학교'),
        ('인하대학교', '인하대학교'),
        ('전남대학교', '전남대학교'),
        ('전북대학교', '전북대학교'),
        ('제주대학교', '제주대학교'),
        ('중앙대학교', '중앙대학교'),
        ('충남대학교', '충남대학교'),
        ('충북대학교', '충북대학교'),
        ('한국외국어대학교', '한국외국어대학교'),
        ('한양대학교', '한양대학교'),
        ('기타대학', '기타 대학'),
    ]


def statistics_aspiration_choice() -> list:
    universities = university_choice()
    universities.insert(0, ('전체', '전체'))
    return universities


def get_aspirations():
    return [aspiration for (aspiration, _) in statistics_aspiration_choice()]


def major_choice() -> list:
    return [
        ('공학', '공학'),
        ('농학', '농학'),
        ('법학', '법학'),
        ('사범', '사범'),
        ('사회', '사회'),
        ('상경', '상경'),
        ('신학', '신학'),
        ('약학', '약학'),
        ('예체능', '예체능'),
        ('의학', '의학'),
        ('인문', '인문'),
        ('자연', '자연'),
        ('기타', '기타'),
    ]


def gpa_type_choice() -> list:
    return [
        (4.0, '4.0 만점'),
        (4.3, '4.3 만점'),
        (4.5, '4.5 만점'),
    ]


def english_type_choice() -> list:
    return [
        ('TOEIC', 'TOEIC'),
        ('TOEFL/IBT', 'TOEFL/IBT'),
        ('TEPS', 'TEPS'),
    ]