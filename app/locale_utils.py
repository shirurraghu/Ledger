from flask_babel import get_locale as babel_get_locale
from flask import session

def get_current_locale():
    return session.get('lang') or str(babel_get_locale())

    
def get_translation_dict(lang):
    if lang == 'en':
        return {
            'total_sales': 'Total Sales',
            'total_expenses': 'Total Expenses',
            'total_purchases': 'Total Purchases',
            'stock_alerts': 'Stock Alerts',
            'recent_activity': 'Recent Activity',
            'type': 'Type',
            'party': 'Party',
            'date': 'Date',
            'amount': 'Amount',
            'payment': 'Payment'
        }

    elif lang == 'hi':
        return {
            'total_sales': 'कुल बिक्री',
            'total_expenses': 'कुल खर्च',
            'total_purchases': 'कुल खरीदारी',
            'stock_alerts': 'स्टॉक अलर्ट',
            'recent_activity': 'हाल की गतिविधि',
            'type': 'प्रकार',
            'party': 'पार्टी',
            'date': 'तारीख',
            'amount': 'राशि',
            'payment': 'भुगतान'
        }

    elif lang == 'kn':
        return {
            'total_sales': 'ಒಟ್ಟು ಮಾರಾಟ',
            'total_expenses': 'ಒಟ್ಟು ಖರ್ಚು',
            'total_purchases': 'ಒಟ್ಟು ಖರೀದಿ',
            'stock_alerts': 'ಸ್ಟಾಕ್ ಎಚ್ಚರಿಕೆ',
            'recent_activity': 'ಇತ್ತೀಚಿನ ಚಟುವಟಿಕೆ',
            'type': 'ಪ್ರಕಾರ',
            'party': 'ಪಕ್ಷ',
            'date': 'ದಿನಾಂಕ',
            'amount': 'ಮೊತ್ತ',
            'payment': 'ಪಾವತಿ'
        }

    elif lang == 'ta':
        return {
            'total_sales': 'மொத்த விற்பனை',
            'total_expenses': 'மொத்த செலவுகள்',
            'total_purchases': 'மொத்த வாங்கல்',
            'stock_alerts': 'கையிருப்பு எச்சரிக்கை',
            'recent_activity': 'சமீபத்திய செயல்கள்',
            'type': 'வகை',
            'party': 'கட்சி',
            'date': 'தேதி',
            'amount': 'தொகை',
            'payment': 'கட்டணம்'
        }

    elif lang == 'ml':
        return {
            'total_sales': 'മൊത്തം വിൽപ്പന',
            'total_expenses': 'മൊത്തം ചെലവുകൾ',
            'total_purchases': 'മൊത്തം വാങ്ങൽ',
            'stock_alerts': 'സ്റ്റോക്ക് അലർട്ടുകൾ',
            'recent_activity': 'സമീപകാല പ്രവർത്തനം',
            'type': 'തരം',
            'party': 'കക്ഷി',
            'date': 'തീയതി',
            'amount': 'തുക',
            'payment': 'പേയ്മെന്റ്'
        }

    elif lang == 'te':
        return {
            'total_sales': 'మొత్తం అమ్మకాలు',
            'total_expenses': 'మొత్తం ఖర్చులు',
            'total_purchases': 'మొత్తం కొనుగోలు',
            'stock_alerts': 'స్టాక్ హెచ్చరికలు',
            'recent_activity': 'ఇటీవలి కార్యకలాపం',
            'type': 'రకం',
            'party': 'పార్టీ',
            'date': 'తేదీ',
            'amount': 'మొత్తం',
            'payment': 'చెల్లింపు'
        }

    elif lang == 'bn':
        return {
            'total_sales': 'মোট বিক্রয়',
            'total_expenses': 'মোট খরচ',
            'total_purchases': 'মোট ক্রয়',
            'stock_alerts': 'স্টক সতর্কতা',
            'recent_activity': 'সাম্প্রতিক কার্যকলাপ',
            'type': 'ধরন',
            'party': 'পক্ষ',
            'date': 'তারিখ',
            'amount': 'পরিমাণ',
            'payment': 'পেমেন্ট'
        }

    else:
        # Default to English
        return {
            'total_sales': 'Total Sales',
            'total_expenses': 'Total Expenses',
            'total_purchases': 'Total Purchases',
            'stock_alerts': 'Stock Alerts',
            'recent_activity': 'Recent Activity',
            'type': 'Type',
            'party': 'Party',
            'date': 'Date',
            'amount': 'Amount',
            'payment': 'Payment'
        }
