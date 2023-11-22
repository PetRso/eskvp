import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Rozdelenie obsahových štandardov do ročníkov")

def load_css(file_name = "style.css"):
    with open(file_name) as f:
        css = f'<style>{f.read()}</style>'
    return css

css = load_css()
st.markdown(css, unsafe_allow_html=True)

@st.cache_data()
def load_standardy():
    """
    sheets_url = st.secrets["public_gsheets_url"]
    """
    sheets_url = st.secrets["public_gsheets_url"]  # existujú dva tvary
    csv_url = sheets_url.replace("edit?usp=sharing", f"gviz/tq?tqx=out:csv&sheet=vzdelavacie_standardy")
    df = pd.read_csv(csv_url).set_index('id')
    df["definicia"] = df["para_html"]
    df = df.fillna('')
    return df

def clean_html(raw_html):
    """Odstráni HTML tagy z vety"""
    cleantext = re.sub('<.*?>', '', raw_html)
    return cleantext

@st.cache_data()
def clean_standardy(definicie):
    """
    definicie = df.para_html
    """
    # odstrani horne indexy
    definicie = definicie.str.replace('<sup>.*?</sup>', '', regex=True)
    definicie = definicie.str.replace('<br>', ' ', regex=False)
    definicie = definicie.str.replace(' ,', '', regex=False)
    definicie = definicie.str.replace(' .', '.', regex=False)

    # odstrani html tagy
    definicie = definicie.str.replace('\*\*', '', regex=True)
    definicie = [clean_html(x) for x in definicie]

    # odstrani znaky na začiatku vety
    definicie = [x[2:] if x[0] == '-' else x for x in definicie]
    definicie = [x[3:] if x[0] == '1' else x for x in definicie]
    definicie = [x.strip() for x in definicie]

    # Všetky veľké písmená a ukončené bodkou, aby všetky štandardy boli formátované rovnako.
    definicie = [x[0].capitalize() + x[1:] for x in definicie]
    definicie = [x + '.' if x[-1] != '.' else x for x in definicie]
    return definicie


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


jazyky = ['Anglický jazyk', 'Francúzsky jazyk', 'Nemecký jazyk', 'Ruský jazyk', 'Španielsky jazyk', 'Taliansky jazyk']

slj_ako_druhy_jazyk = ['Slovenský jazyk ako druhý jazyk', 'Slovenský jazyk a slovenská literatúra']

nabozenstva = ['Náboženstvo Cirkvi bratskej', 'Náboženstvo Gréckokatolíckej cirkvi', 'Náboženstvo Pravoslávnej cirkvi',
               'Náboženstvo Reformovanej kresťanskej cirkvi', 'Náboženstvo Rímskokatolíckej cirkvi',
               'Náboženstvo Evanjelickej cirkvi a. v.']


df = load_standardy()
df["definicia"] = clean_standardy(df["definicia"])


# vyber predmet a cyklus
# predmety = df.predmet.unique()
cykly = [1, 2, 3]
tabs_cykly = {'1. cyklus (r. 1-3)': 1, '2. cyklus (r. 4-5)': 2, '3. cyklus (r. 6-9)': 3}
tabs_cykly_cj = {'1. cyklus (r.1-3)': 1, '2. cyklus (r.4-5)': 2, '3. cyklus - prvý jazyk (r.6-9)': 3, '3. cyklus - druhý jazyk (r.6-9)': 4}

st.sidebar.title('Nástroj na tvorbu učebných osnov')
st.sidebar.info('1. Vyber vzdelávaciu oblasť a cyklus️ 👩🏽‍🏫 \n 1. Priraď obsahové štandardy do ročníkov ☑️ \n 2. Stiahni učebné osnovy v tabuľkovom formáte 📥 🗎')

vo = st.sidebar.selectbox('Vzdelávacia oblasť', vos)
if vos[vo]:
    predmet = st.sidebar.selectbox('Predmet', vos[vo])  # label_visibility='collapsed'
else:
    predmet = vo

if predmet == 'Slovenský jazyk ako druhý jazyk':
    predmet = st.sidebar.selectbox('Slovenský jazyk ako druhý jazyk', slj_ako_druhy_jazyk,
                                   label_visibility='collapsed')
    if predmet == 'Slovenský jazyk ako druhý jazyk':
        tabs_cykly = {'Komunikačná úroveň 1 (základná)': 1, 'Komunikačná úroveň 2 (rozširujúca)': 2}
    elif predmet == 'Cudzí jazyk':
        tabs_cykly = {'1. cyklus (r.1-3)': 1, '2. cyklus (r.4-5)': 2, '3. cyklus - prvý jazyk (r.6-9)': 3,
                      '3. cyklus - druhý jazyk (r.6-9)': 4}
        jazyk = st.sidebar.selectbox('Jazyk', jazyky)
    elif predmet == 'Náboženstvo':
        predmet = st.sidebar.selectbox('Náboženstvo', nabozenstva, label_visibility='collapsed')
    elif predmet == 'Jazyky národnostných menšín':
        predmet = st.sidebar.selectbox('Jazyky národnostných menšín', jazyky_narodnostne, label_visibility='collapsed')


cyklus = tabs_cykly[st.sidebar.selectbox('Cyklus', tabs_cykly.keys())]

# výber dát
dfx = df[df.index.str.contains(f'{predmety_kody[predmet]}{cyklus}-o-')]
dfx = dfx[dfx.typ_standardu != 'Úvod']
dfx = dfx[dfx.tema != 'Úvod']

if predmet == 'Cudzí jazyk':
    jzk = jazyky.copy()  # aby som nemazal selectbox
    jzk.remove(jazyk)
    dfx = dfx[~dfx.typ_standardu.isin(jzk)]  # iba pre vybraný jazyk, alebo pre všetky

# vybrane priradenie do rocnikov
if cyklus == 1:
    cols_rocniky = ['1.', '2.', '3.']
elif cyklus == 2:
    cols_rocniky = ['4.', '5.']
elif cyklus == 3:
    cols_rocniky = ['6.', '7.', '8.', '9.']

dfx.loc[:, cols_rocniky] = True
cols_to_st =  ['definicia'] + cols_rocniky
cols_to_xlsx = ['typ', 'komponent', 'tema', 'typ_standardu', "definicia"]


i_key = 0
for komponent in dfx.komponent.unique():
    st.markdown(f"### {komponent}")
    i_komponent = (dfx.komponent == komponent)
    for tema in dfx.loc[i_komponent,"tema"].unique():
        if tema != '':
            st.markdown(f"#### {tema}")
        i_tema = i_komponent & (dfx.tema == tema)
        for typ_standardu in dfx.loc[i_tema, "typ_standardu"].unique():
            if typ_standardu != '':
                st.markdown(f"##### {typ_standardu}")
            i = i_tema & (dfx.typ_standardu == typ_standardu)
            dfx.loc[i, cols_to_st] = st.data_editor(dfx.loc[i, cols_to_st],
                                            width=1000,
                                            disabled = ['definicia'],
                                            hide_index=True,
                                            key=f"data_editor_{i_key}")
            i_key += 1


def to_excel(df, cols_rocniky):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    for rocnik in cols_rocniky:
        sheet_name = f'{rocnik} ročník'
        df.loc[df[rocnik] == True, cols_to_xlsx].to_excel(writer, index=False, sheet_name=sheet_name)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        # format1 = workbook.add_format({'text_wrap': True})
        worksheet.set_column('A:D', 20)
        worksheet.set_column('E:E', 60)
    writer.close()
    processed_data = output.getvalue()
    return processed_data


df_xlsx = to_excel(dfx, cols_rocniky)
st.download_button(label='📥 Download',
                   data=df_xlsx ,
                   file_name= 'rozdelene_standardy.xlsx')
