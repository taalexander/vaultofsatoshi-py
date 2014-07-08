# -*- coding: utf-8 -*-


def to_iso_datetime(date_str):
        """
        converts date string '12/29/13 03:20:17' -> '2013-12-29T03:20:17Z'
        """
        return (datetime.datetime.strptime(date_str, "%m/%d/%y %H:%M:%S")).isoformat() + 'Z'
