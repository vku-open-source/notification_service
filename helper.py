"""
Copyright (c) VKU.OneLove.
This source code is licensed under the Apache-2.0 license found in the
LICENSE file in the root directory of this source tree.
"""

def normalize_phone_number(phone):
    """
    Chuẩn hóa số điện thoại về định dạng quốc tế của Việt Nam
    Input: Số điện thoại có thể ở các định dạng:
        - '356496966'
        - '0356496966'
        - '84356496966'
    Output: '84356496966'
    """

    phone = ''.join(filter(str.isdigit, str(phone)))
    
    if phone.startswith('0'):
        phone = '84' + phone[1:]

    elif not phone.startswith('84'):
        phone = '84' + phone
        
    return phone
