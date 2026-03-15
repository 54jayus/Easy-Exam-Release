"""高考模式默认配置"""

GAOKAO_TIME_DEFAULTS = {
    "examTimes": {
        "语文": {"date": "2024-06-07", "startTime": "09:00", "endTime": "11:30"},
        "数学": {"date": "2024-06-07", "startTime": "15:00", "endTime": "17:00"},
        "物理历史": {"date": "2024-06-08", "startTime": "09:00", "endTime": "10:15"},
        "英语": {"date": "2024-06-08", "startTime": "15:00", "endTime": "17:00"},
        "化学": {"date": "2024-06-09", "startTime": "08:30", "endTime": "09:45"},
        "地理": {"date": "2024-06-09", "startTime": "11:00", "endTime": "12:15"},
        "政治": {"date": "2024-06-09", "startTime": "14:30", "endTime": "15:45"},
        "生物": {"date": "2024-06-09", "startTime": "17:00", "endTime": "18:15"},
    },
    "selfStudyTimes": {
        "化学": {"date": "2024-06-09", "startTime": "08:30", "endTime": "09:45"},
        "地理": {"date": "2024-06-09", "startTime": "11:00", "endTime": "12:15"},
        "政治": {"date": "2024-06-09", "startTime": "14:30", "endTime": "15:45"},
        "生物": {"date": "2024-06-09", "startTime": "17:00", "endTime": "18:15"},
    }
}

GAOKAO_SUBJECT_ORDER = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']
