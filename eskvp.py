import pandas as pd
import streamlit as st
from rapidfuzz import fuzz
from io import BytesIO

st.set_page_config(page_title="Digitálny ŠVP", page_icon=":ledger:")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

prierez_gram = {'Vizuálna gramotnosť': ':eye:',
                'Čitateľská gramotnosť': ':book:',
                'Digitálna gramotnosť': ':computer:',
                'Finančná gramotnosť': ':chart_with_upwards_trend:',
                'Občianska gramotnosť': ':woman-raising-hand:',
                'Mediálna gramotnosť': ':iphone:',
                'Interkultúrna gramotnosť': ':earth_africa:',
                'Environmentálna gramotnosť': ':seedling:',
                'Sociálna a emocionálna gramotnosť': ':people_holding_hands:'}


prierez_gram_legenda = {'Čitateľská a vizuálna gramotnosť': ':book::eye:',
                'Digitálna gramotnosť': ':computer:',
                'Finančná gramotnosť': ':chart_with_upwards_trend:',
                'Občianska gramotnosť': ':woman-raising-hand::iphone::earth_africa:',  # mediálna a interkultúrna
                'Environmentálna gramotnosť': ':seedling:',
                'Sociálna a emocionálna gramotnosť': ':people_holding_hands:'}

@st.cache_data()
def get_legenda_gramotnost():
    text = '<br>'
    for k, v in prierez_gram_legenda.items():
        text += f"{k} {v} <br>"
    return text

@st.cache_data()
def add_prierezove_gramotnosti(df):
    """Vloží za definíciu ikonku s emoji pre prierezovu gramotnost"""
    i_type = df.index.str.contains('-o-') | df.index.str.contains('-v-')  # nie v cieloch
    for gramotnost in prierez_gram.keys():
        i = (~df[gramotnost].isna()) & i_type
        df.loc[i, "definicia"] = df.loc[i, "definicia"] + f" <span title='{gramotnost}'>{prierez_gram[gramotnost]}</span>"
    return df


def vloz_id(df):
    """Vloží za definíciu ikonku s emoji pre prierezovu gramotnost"""
    i = df.index.str.contains('-o-') | df.index.str.contains('-v-')  # nie v cieloch
    # ak je odrazka v standarde, preskoci ju, aby sa zobrazila v markdown
    df.loc[i, "definicia"] = [f"<span title='{a}'>{b}</span>" if b[0] != '-' else f"- <span title='{a}'>{b[2:]}</span>" for a,b in zip(df.index[i], df.loc[i, "definicia"])]
    return df


@st.cache_data()
def load_standardy():
    """Nahrá SVP v strukturovanej podobne"""
    # sheets_url = st.secrets["public_gsheets_url"]  # existujú dva tvary
    # csv_url = sheets_url.replace("edit?usp=sharing", f"gviz/tq?tqx=out:csv&sheet=vzdelavacie_standardy")
    # df = pd.read_csv(csv_url).set_index('id')
    # df["definicia"] = df["para_html"]
    df = pd.read_csv("standardy_svp.csv", sep='\t').set_index('id')
    df = add_prierezove_gramotnosti(df)
    return df


def standardy_as_items(standardy):
    """Zobrazí štandardy ako odrážky alebo ako samostatnú vetu."""
    # uvodny a stadardy s jednou vetou zacinaju velkym pismenom
    # štandardy ako odrážky
    text = ''
    if standardy.iloc[0][0] == '1':
        # formátovanie cielov
        for i, text_orig in standardy.items():
            text += f'{text_orig}\n'
        st.markdown(text, unsafe_allow_html=True)
    elif standardy.iloc[0][0] == '-':
        # formátovanie výkonových štandardov
        for i, text_orig in standardy.items():
            text += f'{text_orig},\n'
        # posledny bude namiesto ciarky bodka
        text = text[:-2] + '.'
        st.markdown(text, unsafe_allow_html=True)
    else:
        for i, text_orig in standardy.items():
            st.markdown(text_orig, unsafe_allow_html=True)


def divide_by_typ_standardu(df, ziakVie = False):
    df = vloz_id(df)
    typy_standardov = df.typ_standardu.dropna().unique().tolist()
    if len(typy_standardov) > 0:
        for typ_standardu in typy_standardov:  # cinnost, pojem
            # nezobrazuj úvod alebo neopakuj komponent
            if typ_standardu not in ['Úvod', 'none']:
                st.markdown(f'<p style="color: #004280;"><b>{typ_standardu}</b></p>', unsafe_allow_html=True)
                if ziakVie:
                    st.markdown("<b>Žiak vie/dokáže:</b>", unsafe_allow_html=True)
            standardy_as_items(
                df.loc[df.typ_standardu == typ_standardu, "definicia"])
            st.markdown('\n')
    else:
        if ziakVie:
            st.markdown("<b>Žiak vie/dokáže:</b>", unsafe_allow_html=True)
        standardy_as_items(df["definicia"])


def export_to_excel(df):
    """Úprava excel tabuľky na export."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data


# @st.cache_data()
def tranform_to_export(df):
    """Vyčistí definície pre účely exportu."""
    # bez uvodov a hlavnych cielov
    df = df[(df.typ_standardu != 'Úvod')]
    df = df[(df.tema != 'Úvod')]
    df = df[~df.index.str.contains('-hc-')]
    df = df.rename(columns={'typ_standardu': 'druh', 'definicia_clean': 'definicia standardu'})

    # vyber stlpcov
    cols_to_xlsx = ['id', 'typ', 'komponent', 'tema', 'druh', 'definicia standardu']
    df = export_to_excel(df.reset_index()[cols_to_xlsx])
    return df


def show_search_results(df):
    """
    Zobrazenie výsledkov vyhľadávania.

    definicia = 'Kriticky posudzovať využitie výsledkov (vedeckého) výskumu pre človeka a spoločnosť.'
    zaradenie = 'Výtvarná výchova | 3. cyklus | Obsahový štandard | Osobnosť | vv3-o-033'
    """
    for id, row in df.iterrows():
        definicia = row.definicia_clean.strip()
        st.markdown(f"<b><span title='{id}'>{definicia}</span></b>",
                    unsafe_allow_html=True)
        zaradenie = f"{row.predmet} | {row.cyklus}. cyklus | {row.typ} | {row.komponent} | {row.tema} | {row.typ_standardu} | {id}"
        zaradenie = zaradenie.replace("none", "")
        zaradenie = zaradenie.replace("|  |  |","|").replace("|  |","|")
        st.markdown(zaradenie, unsafe_allow_html=True)
        st.markdown('---')


def vyber_podla_predmetu(df, options):
    """Vyber standardov podla predmetov chema, fyzika alebo biologia."""
    i_vs = df.index.str.contains('-v-')

    if 'Chémia' in options:
        i_ch = df.definicia.str.contains('<sup>CH</sup>')
    else:
        i_ch = df.definicia.str.contains('xxxx')  # TODO all false
    if 'Fyzika' in options:
        i_f = df.definicia.str.contains('<sup>F</sup>')
    else:
        i_f = df.definicia.str.contains('xxxx')
    if 'Biológia' in options:
        i_b = df.definicia.str.contains('<sup>B</sup>')
    else:
        i_b = df.definicia.str.contains('xxxx')

    df = df[i_ch | i_b | i_f | i_vs]

    # aby bola aj čiarka medzi F,CH,B bola v hornom indexe
    df["definicia"] = df["definicia"].str.replace('</sup>, <sup>', ', ', regex=False)
    return df


# definícia predmetov
vos = {'Jazyk a komunikácia': ['Slovenský jazyk a literatúra', 'Jazyky národnostných menšín',
                               'Slovenský jazyk ako druhý jazyk', 'Cudzí jazyk'],
       'Matematika a informatika': ['Matematika', 'Informatika'],
       'Človek a príroda': [],
       'Človek a spoločnosť': ['Človek a spoločnosť', 'Náboženstvo'],
       'Človek a svet práce': [],
       'Umenie a kultúra': ['Hudobná výchova', 'Výtvarná výchova'],
       'Zdravie a pohyb': []}

jazyky_narodnostne = ['Maďarský jazyk a literatúra', 'Nemecký jazyk a literatúra', 'Rómsky jazyk a literatúra',
                      'Rusínsky jazyk a literatúra', 'Ruský jazyk a literatúra', 'Ukrajinský jazyk a literatúra']

jazyky = ['Anglický jazyk', 'Francúzsky jazyk', 'Nemecký jazyk', 'Ruský jazyk', 'Španielsky jazyk', 'Taliansky jazyk']

slj_ako_druhy_jazyk = ['Slovenský jazyk ako druhý jazyk', 'Slovenský jazyk a slovenská literatúra']

nabozenstva = ['Náboženstvo Cirkvi bratskej', 'Náboženstvo Gréckokatolíckej cirkvi', 'Náboženstvo Pravoslávnej cirkvi',
               'Náboženstvo Reformovanej kresťanskej cirkvi', 'Náboženstvo Rímskokatolíckej cirkvi',
               'Náboženstvo Evanjelickej cirkvi a. v.']

# definícia skratiek pre id
predmety_kody = {'Slovenský jazyk a literatúra': 'sk',
                 'Maďarský jazyk a literatúra': 'hu',
                 'Nemecký jazyk a literatúra': 'de',
                 'Rómsky jazyk a literatúra': 'ry',
                 'Rusínsky jazyk a literatúra': 'ri',
                 'Ruský jazyk a literatúra': 'ru',
                 'Ukrajinský jazyk a literatúra': 'uk',
                 'Slovenský jazyk a slovenská literatúra': 'sj',
                 'Slovenský jazyk ako druhý jazyk': 'dj',
                 'Cudzí jazyk': 'cj',
                 'Matematika': 'mt',
                 'Informatika': 'if',
                 'Človek a spoločnosť': 'cs',
                 'Človek a príroda': 'cp',
                 'Človek a svet práce': 'sp',
                 'Hudobná výchova': 'hv',
                 'Výtvarná výchova': 'vv',
                 'Zdravie a pohyb': 'zp',
                 'Náboženstvo Cirkvi bratskej': 'br',
                 'Náboženstvo Gréckokatolíckej cirkvi': 'gr',
                 'Náboženstvo Pravoslávnej cirkvi': 'pr',
                 'Náboženstvo Reformovanej kresťanskej cirkvi': 'rf',
                 'Náboženstvo Rímskokatolíckej cirkvi': 'rk',
                 'Náboženstvo Evanjelickej cirkvi a. v.': 'ev'}

predmety_vykony_pod_cielmi = ['Človek a príroda', 'Informatika', 'Matematika', 'Človek a spoločnosť']
predmet_bez_delenia_obsah_standardov = ['Hudobná výchova', 'Výtvarná výchova', 'Zdravie a pohyb'] + nabozenstva

df = load_standardy()

cykly = [1, 2, 3]
tabs_cykly = {'1. cyklus (r. 1-3)': 1, '2. cyklus (r. 4-5)': 2, '3. cyklus (r. 6-9)': 3}
tabs_cykly_cj = {'1. cyklus (r.1-3)': 1, '2. cyklus (r.4-5)': 2, '3. cyklus - prvý jazyk (r.6-9)': 3, '3. cyklus - druhý jazyk (r.6-9)': 4}

link = 'https://www.minedu.sk/data/files/11808_statny-vzdelavaci-program-pre-zakladne-vzdelavanie-cely.pdf'
st.sidebar.markdown(f'# <a style="text-decoration: none; color: #004280;" href={link}>Digitálna verzia štátneho vzdelávacieho programu 2023</a>', unsafe_allow_html=True)


query = st.sidebar.text_input('Vyhľadávanie', '', key=1)
st.sidebar.markdown("---")


if query:
    # Vyhľadávanie v štandardoch
    st.sidebar.warning(f'Pre návrat na ŠVP zmažte text vo vyhľadávaní.')
    if len(query) < 3:
        st.sidebar.warning('Hľadaný text musí mať aspoň 3 znaky')
    else:
        # vyhľadávanie 1:1
        res = df[df.definicia_clean.str.contains(query)]
        st.sidebar.info(f'Našlo sa {len(res)} podobných záznamov')
        show_search_results(res.head(50).fillna(''))
        if len(res) > 50:
            st.warning("Výsledky vyhľadávania boli skrátené na 50 záznamov.")

        # fuzzy search - ak sa nájde priamou cestou viac ako 5 nájdení
        if len(res) < 5:
            df["res"] = [fuzz.token_set_ratio(t, query) for t in df.definicia_clean]  # TODO use processes
            df = df.sort_values("res", ascending=False)
            res2 = df.loc[df.res > 50].fillna('')
            res2 = res2.drop(res.index, errors='ignore')  # odstráni už vyhľadané záznamy cez exact match
            if len(res2) > 0:
                st.info("Výsledky vyhľadávania na základe podobnosti")
                show_search_results(res2.head(30))
                if len(res2) > 30:
                    st.warning("Výsledky vyhľadávania boli skrátené na 30 záznamov.")
else:
    # Prehliadanie ŠVP
    # SIDE BAR


    # Výber vzdelávacej oblasti
    vo = st.sidebar.selectbox('Vzdelávacia oblasť', vos)
    if vos[vo]:
        # Výber predmetu pre vzdelávaciu oblasť
        predmet = st.sidebar.selectbox('Predmet', vos[vo])
    else:
        # Vzdelávacia oblasť a predmet majú rovnaký názov
        predmet = vo

    # špecifiká predmetov
    if predmet == 'Slovenský jazyk ako druhý jazyk':
        predmet = st.sidebar.selectbox('Slovenský jazyk ako druhý jazyk', slj_ako_druhy_jazyk, label_visibility='collapsed')
        if predmet == 'Slovenský jazyk ako druhý jazyk':
            tabs_cykly = {'Komunikačná úroveň 1 (základná)': 1, 'Komunikačná úroveň 2 (rozširujúca)': 2}
    elif predmet == 'Cudzí jazyk':
        tabs_cykly = tabs_cykly_cj
        jazyk = st.sidebar.selectbox('Jazyk', jazyky)
    elif predmet == 'Náboženstvo':
        predmet = st.sidebar.selectbox('Náboženstvo', nabozenstva, label_visibility='collapsed')
    elif predmet == 'Jazyky národnostných menšín':
        predmet = st.sidebar.selectbox('Jazyky národnostných menšín', jazyky_narodnostne, label_visibility='collapsed')

    # Výber cyklu
    cyklus_vyber = st.sidebar.selectbox('Cyklus', tabs_cykly.keys())
    cyklus = tabs_cykly[cyklus_vyber]

    # filter prierezovej gramotnosti
    p_gram = st.sidebar.selectbox('Prierezová gramotnosť', ['Všetky'] + list(prierez_gram_legenda.keys()), index=0)

    # Výber dát pre predmet a cyklus
    df = df[df.index.str.contains(f'{predmety_kody[predmet]}{cyklus}')]

    # cudzí jazyk sa delí ešte podľa cudzích jazykov
    if predmet == 'Cudzí jazyk':
        jzk = jazyky.copy()  # aby som nemazal selectbox
        jzk.remove(jazyk)
        df = df[~df.typ_standardu.isin(jzk)]  # iba pre vybraný jazyk, alebo pre všetky

    # MAIN PANEL
    # Nadpis predmetu
    st.markdown(f'###  {predmet} - {cyklus_vyber}')
    if p_gram == 'Všetky':   # prierezova gramotnost
        # Či sú výkonové štandardy pod cieľmi alebo nie
        if predmet in predmety_vykony_pod_cielmi:
            st.markdown("#### Ciele a výkonové štandardy")
        else:
            st.markdown("#### Ciele")

        # Hlavný cieľ je podfarbený modrou.
        hlavny_ciel = df.loc[df.index.str.contains('-hc-'), "definicia"]
        if not hlavny_ciel.empty:
            st.info(hlavny_ciel.iloc[0])  # Môže byť iba jeden hlavný cieľ.

        # Zoznam cieľov
        ciele = df.loc[df.index.str.contains("-c-"), "definicia"]
        with st.expander(f"Ciele vzdelávania"):
            standardy_as_items(ciele)

        # Vzdelávacie štandardy
        if predmet in predmety_vykony_pod_cielmi:
            # Vykonove standardy su zaradene pod celmi
            with st.expander(f"Výkonové štandardy"):
                divide_by_typ_standardu(df.loc[df.index.str.contains("-v-")], True)
            st.markdown("\n")
            st.markdown("#### Obsahové štandardy pre komponenty")

            # Úvod k obsahovému štandardu (človek a príroda) je nad témami
            if predmet == 'Človek a príroda':
                i_uvod_os = (df.typ_standardu == 'Úvod') & df.index.str.contains('-o-')
                uvod_obsahoveho_standardu = df.loc[i_uvod_os,"definicia"]
                if not uvod_obsahoveho_standardu.empty:
                    st.markdown(uvod_obsahoveho_standardu.iloc[0], unsafe_allow_html=True)
        else:
            # Vykonove standardy su zaradene pod komponentmi
            st.markdown("#### Vzdelávacie štandardy pre komponenty")

        # Rozdelenie podľa vnorených predmetov človek a príroda
        if (predmet == 'Človek a príroda') & (cyklus == 3):
            predmety_cap = ['Fyzika', 'Chémia', 'Biológia']
            vybrane_predmety = st.multiselect('Ktoré predmety vás zaujímajú?', predmety_cap, predmety_cap)
            df = vyber_podla_predmetu(df, vybrane_predmety)

        # Výnimka pre cudzí jazyk
        if cyklus_vyber == '3. cyklus - druhý jazyk (r.6-9)':
            st.tabs(['Komunikačné jazykové činnosti (recepcia, produkcia, interakcia)'])
            st.info(df.loc[df.typ == 'Výkonový a obsahový štandard', 'definicia'][0])
            st.stop()

        # Komponenty pre vybraný predmet a cyklus
        komponenty = df[df.index.str.contains('-o-')].komponent.dropna().unique().tolist()

        if len(komponenty) > 0:
            tabs_komponenty = st.tabs(komponenty)
        else:
            st.error("Pre výber sa nenašli komponenty.")
            st.stop()

        for komponent, tab_komponent in zip(komponenty, tabs_komponenty):
            with tab_komponent:
                if not predmet in predmety_vykony_pod_cielmi:
                    with st.expander("Výkonové štandardy"):
                        dfy = df[(df.komponent == komponent) & df.index.str.contains('-v-')]
                        if dfy.empty:
                            dfy = df[df.index.str.contains('-v-')]
                        divide_by_typ_standardu(dfy, True)
                    if predmet not in predmet_bez_delenia_obsah_standardov:
                        st.markdown("<h5 style='text-align: center;'>Obsahové štandardy</h5>", unsafe_allow_html=True)

                # Obsahove standardy
                dfy = df[(df.komponent == komponent) & df.index.str.contains('-o-')]

                # Témy v obsahových štandardoch
                temy = dfy.tema.dropna().unique().tolist()
                if len(temy) > 0:
                    # Temy sa zobrazuju ako expander
                    for tema in temy:
                        with st.expander(f'{tema}'):
                            dfl = dfy[dfy.tema == tema]
                            divide_by_typ_standardu(dfl)
                else:
                    # Predmet nemá témy
                    if not predmet in predmety_vykony_pod_cielmi:
                        with st.expander("Obsahový štandard"):
                            divide_by_typ_standardu(dfy)
                    else:
                        divide_by_typ_standardu(dfy)

        # download button: export standardov do xlsx
    else:
        # zobrazenie prierezovej gramotnosti
        st.info(f"{p_gram} {prierez_gram_legenda[p_gram]} sa môže rozvíjať v týchto obsahových štandardoch.")

        if p_gram == 'Občianska gramotnosť':
            df = df[~df['Občianska gramotnosť'].isna() | ~df['Mediálna gramotnosť'].isna() |  ~df['Interkultúrna gramotnosť'].isna()]
        elif p_gram == 'Čitateľská a vizuálna gramotnosť':
            df = df[(~df['Čitateľská gramotnosť'].isna()) | (~df['Vizuálna gramotnosť'].isna())]
        else:
            df = df[~df[p_gram].isna()]

        df = df.loc[df.index.str.contains('-o-')].fillna('')

        for komponent in df.komponent.unique():
            st.markdown(f"### {komponent}")
            i_komponent = (df.komponent == komponent)
            for tema in df.loc[i_komponent, "tema"].unique():
                if tema not in ['', 'none']:
                    st.markdown(f"#### {tema}")
                i_tema = i_komponent & (df.tema == tema)
                for typ_standardu in df.loc[i_tema, "typ_standardu"].unique():
                    if typ_standardu not in ['', 'none']:
                        st.markdown(f"##### {typ_standardu}")
                    i = i_tema & (df.typ_standardu == typ_standardu)
                    for definicia in df.loc[i, "definicia"]:
                        st.markdown(definicia, unsafe_allow_html=True)

    legenda_gramotnosti = get_legenda_gramotnost()
    st.sidebar.markdown(legenda_gramotnosti, unsafe_allow_html=True)

    if p_gram == 'Všetky':
        st.sidebar.divider()
        st.sidebar.download_button(label='📥 Stiahni tabuľku (xlsx)',
                                   data=tranform_to_export(df),
                                   file_name=f'standardy_{predmet}_c{cyklus}.xlsx')
