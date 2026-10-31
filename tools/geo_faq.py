"""GEO/AEO: қала беттеріне (Атыраудан басқа) блок-жауап (#answer) және FAQ (#faq).
seo.py шақырады (қайта іске қосуға болады: бұрынғы блоктар ауыстырылады); аудармасын city_rules.py береді.
Атыраудың өз мәтіні бар (atyrau.html-де қолмен жазылған) — оған тиіспейміз."""
import re

CSS = ('  #answer, #faq { margin-bottom: 12px; }\n  #answer h2, #faq h2 { font-size: 18px; margin: 0 0 6px; }\n'
       '  #answer p, #faq p { margin: 0; font-size: 14.5px; line-height: 1.55; }\n  #faq h3 { font-size: 15px; font-weight: 700; margin: 14px 0 4px; }\n')
H2_FAQ = ('Жиі қойылатын сұрақтар', 'Частые вопросы', 'Frequently asked questions')
Q_SRC = ('Деректер қайдан алынады?', 'Откуда берутся данные?', 'Where does the data come from?')
A_SRC = ('Ауа сапасы — Қазгидромет бекеттері (ecodata.kz), сағат сайын. Жел мен метеорология — Open-Meteo.',
         'Качество воздуха — посты Казгидромета (ecodata.kz), каждый час. Ветер и метеорология — Open-Meteo.',
         'Air quality — Kazhydromet stations (ecodata.kz), every hour. Wind and meteorology — Open-Meteo.')
Q_SUBS = ('Бекеттер қандай заттарды өлшейді?', 'Какие вещества измеряют посты?', 'Which substances do the stations measure?')
Q_LIM = ('Ластану шекті мәннен асқанын қалай білуге болады?', 'Как понять, что загрязнение превысило предельную норму?',
         'How can I tell if pollution exceeds the limit?')
A_LIM = ('Сайт өлшемдерді ҚР ДСМ-70 бұйрығындағы (02.08.2022) ең жоғары бір реттік ПДК-мен салыстырады; бекеттер сағаттық мән береді, сондықтан салыстыру шамамен. Нәтиже — ресми өлшем емес; денсаулыққа қатысты шешімді мамандардан сұраңыз.',
         'Сайт сравнивает измерения с максимальной разовой ПДК из приказа МЗ РК ДСМ-70 (02.08.2022); посты дают почасовые значения, поэтому сравнение приблизительное. Результат — не официальное измерение; по вопросам здоровья обращайтесь к специалистам.',
         'The site compares measurements with the maximum single-exposure limit (MPC) from order DSM-70 (02.08.2022) of Kazakhstan; stations give hourly values, so the comparison is approximate. The result is not an official measurement; for health questions, consult a specialist.')


def h2_answer(loc, N, E):
    return (f'{loc} ауа сапасы қандай?', f'Какое сейчас качество воздуха в городе {N}?', f'What is the air quality in {E} now?')


def p_answer(N, E):
    return (f'Бұл бет {N} қаласының ауа сапасын Қазгидромет бекеттерінің сағаттық өлшемдері бойынша көрсетеді: қазіргі деңгей, соңғы сағаттардағы өзгеріс және жел бағыты. Жел деректері ластанудың ықтимал бағытын бағалауға көмектеседі, бірақ нақты көзді дәлелдемейді. Қажет сағатты слайдермен таңдап, картадан қарауға болады.',
            f'Эта страница показывает качество воздуха в городе {N} по почасовым измерениям постов Казгидромета: текущий уровень, изменение за последние часы и направление ветра. Данные о ветре помогают оценить вероятное направление загрязнения, но не доказывают конкретный источник. Нужный час можно выбрать ползунком и посмотреть на карте.',
            f'This page shows air quality in {E} based on hourly measurements from Kazhydromet stations: the current level, the change over recent hours and the wind direction. Wind data helps estimate the likely direction of pollution but does not prove a specific source. Pick the hour with the slider and view it on the map.')


def a_subs(subs):
    s = ', '.join(subs)
    return (f'Бұл қаладағы бекеттер өлшейтін заттар: {s}.', f'Вещества, которые измеряют посты этого города: {s}.',
            f'Substances measured by the stations in this city: {s}.')


def apply(text, N, loc, subs):
    """kk бет мәтініне #answer (main-ның басына), #faq (main соңына) және CSS қояды; бұрынғыларын ауыстырады."""
    text = re.sub(r'    <section class="card" id="(?:answer|faq)">.*?</section>\n', '', text, flags=re.S)
    ans = (f'    <section class="card" id="answer">\n      <h2>{h2_answer(loc, N, N)[0]}</h2>\n      <p>{p_answer(N, N)[0]}</p>\n    </section>\n')
    qa = lambda q, a: f'      <div class="qa"><h3>{q}</h3>\n        <p>{a}</p></div>\n'
    faq = ('    <section class="card" id="faq">\n      <h2>' + H2_FAQ[0] + '</h2>\n' + qa(Q_SRC[0], A_SRC[0]) +
           (qa(Q_SUBS[0], a_subs(subs)[0]) if subs else '') + qa(Q_LIM[0], A_LIM[0]) + '    </section>\n')
    a, b, c = '  <div>\n    <div id="map"></div>\n', '    </details>\n  </div>\n</main>', '  h2 { font-weight: 700; }\n'
    assert text.count(a) == 1 and text.count(b) == 1 and text.count(c) == 1
    text = text.replace(a, '  <div>\n' + ans + '    <div id="map"></div>\n', 1).replace(b, '    </details>\n' + faq + '  </div>\n</main>', 1)
    if '#answer, #faq' not in text:
        text = text.replace(c, c + CSS, 1)
    return text
