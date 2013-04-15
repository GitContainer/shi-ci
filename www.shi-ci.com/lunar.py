#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

g_tiangan = u'甲乙丙丁戊己庚辛壬癸'
g_dizhi = u'子丑寅卯辰巳午未申酉戌亥'

g_months = (u'正月', u'二月', u'三月', u'四月', u'五月', u'六月', u'七月', u'八月', u'九月', u'十月', u'十一月', u'腊月')
g_days = (u'初一', u'初二', u'初三', u'初四', u'初五', u'初六', u'初七', u'初八', u'初九', u'初十', u'十一', u'十二', u'十三', u'十四', u'十五', u'十六', u'十七', u'十八', u'十九', u'二十', u'廿一', u'廿二', u'廿三', u'廿四', u'廿五', u'廿六', u'廿七', u'廿八', u'廿九', u'三十')

g_lunar_month_days = [
    0xF0EA4, 0xF1D4A, 0x52C94, 0xF0C96, 0xF1536, 0x42AAC, 0xF0AD4, 0xF16B2, 0x22EA4, 0xF0EA4,  # 1901-1910
    0x6364A, 0xF164A, 0xF1496, 0x52956, 0xF055A, 0xF0AD6, 0x216D2, 0xF1B52, 0x73B24, 0xF1D24,  # 1911-1920
    0xF1A4A, 0x5349A, 0xF14AC, 0xF056C, 0x42B6A, 0xF0DA8, 0xF1D52, 0x23D24, 0xF1D24, 0x61A4C,  # 1921-1930
    0xF0A56, 0xF14AE, 0x5256C, 0xF16B4, 0xF0DA8, 0x31D92, 0xF0E92, 0x72D26, 0xF1526, 0xF0A56,  # 1931-1940
    0x614B6, 0xF155A, 0xF0AD4, 0x436AA, 0xF1748, 0xF1692, 0x23526, 0xF152A, 0x72A5A, 0xF0A6C,  # 1941-1950
    0xF155A, 0x52B54, 0xF0B64, 0xF1B4A, 0x33A94, 0xF1A94, 0x8152A, 0xF152E, 0xF0AAC, 0x6156A,  # 1951-1960
    0xF15AA, 0xF0DA4, 0x41D4A, 0xF1D4A, 0xF0C94, 0x3192E, 0xF1536, 0x72AB4, 0xF0AD4, 0xF16D2,  # 1961-1970
    0x52EA4, 0xF16A4, 0xF164A, 0x42C96, 0xF1496, 0x82956, 0xF055A, 0xF0ADA, 0x616D2, 0xF1B52,  # 1971-1980
    0xF1B24, 0x43A4A, 0xF1A4A, 0xA349A, 0xF14AC, 0xF056C, 0x60B6A, 0xF0DAA, 0xF1D92, 0x53D24,  # 1981-1990
    0xF1D24, 0xF1A4C, 0x314AC, 0xF14AE, 0x829AC, 0xF06B4, 0xF0DAA, 0x52D92, 0xF0E92, 0xF0D26,  # 1991-2000
    0x42A56, 0xF0A56, 0xF14B6, 0x22AB4, 0xF0AD4, 0x736AA, 0xF1748, 0xF1692, 0x53526, 0xF152A,  # 2001-2010
    0xF0A5A, 0x4155A, 0xF156A, 0x92B54, 0xF0BA4, 0xF1B4A, 0x63A94, 0xF1A94, 0xF192A, 0x42A5C,  # 2011-2020
    0xF0AAC, 0xF156A, 0x22B64, 0xF0DA4, 0x61D52, 0xF0E4A, 0xF0C96, 0x5192E, 0xF1956, 0xF0AB4,  # 2021-2030
    0x315AC, 0xF16D2, 0xB2EA4, 0xF16A4, 0xF164A, 0x63496, 0xF1496, 0xF0956, 0x50AB6, 0xF0B5A,  # 2031-2040
    0xF16D4, 0x236A4, 0xF1B24, 0x73A4A, 0xF1A4A, 0xF14AA, 0x5295A, 0xF096C, 0xF0B6A, 0x31B54,  # 2041-2050
    0xF1D92, 0x83D24, 0xF1D24, 0xF1A4C, 0x614AC, 0xF14AE, 0xF09AC, 0x40DAA, 0xF0EAA, 0xF0E92,  # 2051-2060
    0x31D26, 0xF0D26, 0x72A56, 0xF0A56, 0xF14B6, 0x52AB4, 0xF0AD4, 0xF16CA, 0x42E94, 0xF1694,  # 2061-2070
    0x8352A, 0xF152A, 0xF0A5A, 0x6155A, 0xF156A, 0xF0B54, 0x4174A, 0xF1B4A, 0xF1A94, 0x3392A,  # 2071-2080
    0xF192C, 0x7329C, 0xF0AAC, 0xF156A, 0x52B64, 0xF0DA4, 0xF1D4A, 0x41C94, 0xF0C96, 0x8192E,  # 2081-2090
    0xF0956, 0xF0AB6, 0x615AC, 0xF16D4, 0xF0EA4, 0x42E4A, 0xF164A, 0xF1516, 0x22936,           # 2090-2099
]

START_YEAR, END_YEAR = 1901, 1900 + len(g_lunar_month_days)
LUNAR_START_DATE, SOLAR_START_DATE = (1901, 1, 1), datetime(1901,2,19) # 1901年正月初一的公历日期为1901/2/19
LUNAR_END_DATE, SOLAR_END_DATE = (2099, 12, 30), datetime(2100,2,18) # 2099年12月30的公历日期是2100/2/8

def date_diff(tm):
    return (tm - SOLAR_START_DATE).days

def get_leap_month(lunar_year):
    return (g_lunar_month_days[lunar_year-START_YEAR] >> 16) & 0x0F

def lunar_month_days(lunar_year, lunar_month):
    return 29 + ((g_lunar_month_days[lunar_year-START_YEAR] >> lunar_month) & 0x01)

def lunar_year_days(year):
    days = 0
    months_day = g_lunar_month_days[year - START_YEAR] 
    for i in range(1, 13 if get_leap_month(year) == 0x0F else 14):
        day = 29 + ((months_day>>i)&0x01)
        days += day
    return days

def get_lunar_date_name(lunar_date):
    '''
    Return name of lunar date.

    >>> get_lunar_date_name((2013, 2, 24, False))
    (u'\u7532\u5348', u'\u4e8c\u6708', u'\u5eff\u56db')
    '''
    year, month, day, leap = lunar_date
    return name_of_year(year), name_of_month(month, leap), name_of_day(day)

def get_lunar_date(t=None):
    '''
    Return lunar date as (year, month, day, isLeap).

    >>> get_lunar_date(datetime(2013, 4, 4))
    (2013, 2, 24, False)
    >>> get_lunar_date(datetime(2013, 4, 11))
    (2013, 3, 2, False)
    '''
    tm = t if t else datetime.now()
    if (tm < SOLAR_START_DATE or tm > SOLAR_END_DATE):
        raise Exception('out of range')

    span_days = date_diff(tm)

    year, month, day = START_YEAR, 1, 1
    tmp = lunar_year_days(year)
    while span_days >= tmp:
        span_days -= tmp
        year += 1
        tmp = lunar_year_days(year)

    leap = False
    tmp = lunar_month_days(year, month)
    while span_days >= tmp:
        span_days -= tmp
        month += 1
        tmp = lunar_month_days(year, month)
    leap_month = get_leap_month(year)
    if  month > leap_month:
        month -= 1
        if month == leap_month:
            leap = True

    day += span_days
    return (year, month, day, leap)

def name_of_month(month, leap):
    if leap:
        return u'闰%s' % g_months[month-1]
    return g_months[month-1]

def name_of_day(day):
    '''
    '''
    return g_days[day-1]

def name_of_year(year):
    if (year < 1204 or year > 2099):
        raise Exception('out of range')
    return u'%s%s' % (g_tiangan[(year - 3) % 10], g_dizhi[(year - 3) % 12])

_JIEQI = {
    20130204: u'立春',
    20130218: u'雨水',
    20130305: u'惊蛰',
    20130320: u'春分',
    20130404: u'清明',
    20130420: u'谷雨',
    20130505: u'立夏',
    20130521: u'小满',
    20130605: u'芒种',
    20130621: u'夏至',
    20130707: u'小暑',
    20130722: u'大暑',
    20130807: u'立秋',
    20130823: u'处暑',
    20130907: u'白露',
    20130923: u'秋分',
    20131008: u'寒露',
    20131023: u'霜降',
    20131107: u'立冬',
    20131122: u'小雪',
    20131207: u'大雪',
    20131222: u'冬至',
    20140105: u'小寒',
    20140120: u'大寒',

    20140204: u'立春',
    20140219: u'雨水',
    20140306: u'惊蛰',
    20140321: u'春分',
    20140405: u'清明',
    20140420: u'谷雨',
    20140505: u'立夏',
    20140521: u'小满',
    20140606: u'芒种',
    20140621: u'夏至',
    20140707: u'小暑',
    20140723: u'大暑',
    20140807: u'立秋',
    20140823: u'处暑',
    20140908: u'白露',
    20140923: u'秋分',
    20141008: u'寒露',
    20141023: u'霜降',
    20141107: u'立冬',
    20141122: u'小雪',
    20141207: u'大雪',
    20141222: u'冬至',
    20150105: u'小寒',
    20150120: u'大寒',

    20150204: u'立春',
    20150219: u'雨水',
    20150306: u'惊蛰',
    20150321: u'春分',
    20150405: u'清明',
    20150420: u'谷雨',
    20150506: u'立夏',
    20150521: u'小满',
    20150606: u'芒种',
    20150622: u'夏至',
    20150707: u'小暑',
    20150723: u'大暑',
    20150808: u'立秋',
    20150823: u'处暑',
    20150908: u'白露',
    20150923: u'秋分',
    20151008: u'寒露',
    20151024: u'霜降',
    20151108: u'立冬',
    20151122: u'小雪',
    20151207: u'大雪',
    20151222: u'冬至',
    20160106: u'小寒',
    20160120: u'大寒',
}

def get_jieqi(y, m, d):
    return _JIEQI.get(10000 * y + 100 * m + d)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import unittest
    class Test(unittest.TestCase):
        def test_get_lunar_date_out_of_range(self):
            self.assertRaises(Exception, get_lunar_date, datetime(1898,12,25))
            self.assertRaises(Exception, get_lunar_date, datetime(2100,3,5))

        def test_get_lunar_date(self):
            self.assertEqual((1987, 6, 1, True), get_lunar_date(datetime(1987, 7, 26)))
            self.assertEqual((1987, 6, 1, False), get_lunar_date(datetime(1987, 6, 26)))
            self.assertEqual((1950, 5, 12, False), get_lunar_date(datetime(1950, 6, 26)))
            self.assertEqual((1985, 2, 29, False),  get_lunar_date(datetime(1985, 4, 18)))
            self.assertEqual((2011, 12, 29, False),  get_lunar_date(datetime(2012, 1, 22)))
            self.assertEqual((2099, 11, 20, False), get_lunar_date(datetime(2099,12,31)))

    unittest.main()
