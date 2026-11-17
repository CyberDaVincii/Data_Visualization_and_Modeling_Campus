"""Personal dashboard: which U.S. industries are adopting AI fastest? (Census BTOS data)

The page theme lives in assets/ (theme.css and fireflies.js), which Dash loads
automatically. build_dashboard is the checked function from the Week 4 lab notebook.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html


def build_dashboard(data):
    """Dashboard for the Census AI use analysis.

    data is the original workbook: the dictionary of sheets returned by
    pd.read_excel(path, sheet_name=None, dtype=str). The function repeats the
    notebook's preparation on its own copies of the sheets.
    """
    names = {
        '11': 'Agriculture, forestry, fishing', '21': 'Mining, oil and gas',
        '22': 'Utilities', '23': 'Construction', '31': 'Manufacturing',
        '42': 'Wholesale trade', '44': 'Retail trade', '48': 'Transportation and warehousing',
        '51': 'Information', '52': 'Finance and insurance', '53': 'Real estate and rental',
        '54': 'Professional and technical services', '55': 'Management of companies',
        '56': 'Administrative and waste services', '61': 'Educational services',
        '62': 'Health care and social assistance', '71': 'Arts, entertainment, recreation',
        '72': 'Accommodation and food services', '81': 'Other services',
    }
    questions = {'7': 'ai_use', '28': 'expected_use'}
    keys = ['Sector', 'Question ID', 'Answer']
    estimates = data['Response Estimates'].copy()
    std_errors = data['Response Standard Errors'].copy()
    dates = data['Collection and Reference Dates'].copy()
    cycle_columns = [c for c in estimates.columns if str(c).isdigit()]

    # Preparation (same steps as the notebook).
    def yes_answers(table):
        keep = (table['Sector'].fillna('').str.fullmatch(r'\d\d')
                & table['Question ID'].isin(list(questions))
                & table['Answer'].eq('Yes'))
        return table.loc[keep].melt(id_vars=keys, value_vars=cycle_columns,
                                    var_name='cycle', value_name='text')

    def to_percent(text):
        return pd.to_numeric(text.str.rstrip('%'), errors='coerce')

    long = yes_answers(estimates).merge(yes_answers(std_errors), on=keys + ['cycle'],
                                        suffixes=('_estimate', '_se'))
    long = long[long['text_estimate'].ne('.')].copy()
    long['percent'] = to_percent(long['text_estimate'])
    long['std_error'] = to_percent(long['text_se'])
    long['measure'] = long['Question ID'].map(questions)
    prepared = long.pivot(index=['Sector', 'cycle'], columns='measure', values=['percent', 'std_error'])
    prepared.columns = [f"{measure}_{'pct' if stat == 'percent' else 'se'}" for stat, measure in prepared.columns]
    prepared = prepared.reset_index()
    dates['cycle'] = pd.to_numeric(dates['Smpdt'], errors='coerce').astype('Int64').astype(str)
    dates['ref_start'] = pd.to_datetime(dates['Reference Period Start'], errors='coerce')
    dates['ref_end'] = pd.to_datetime(dates['Ref End'], errors='coerce')
    prepared = prepared.merge(dates[['cycle', 'ref_start', 'ref_end']], on='cycle', how='left')
    prepared['industry'] = prepared['Sector'].map(names)
    suppressed_share = prepared.groupby('Sector')['ai_use_pct'].apply(lambda s: s.isna().mean())
    prepared = prepared[~prepared['Sector'].isin(suppressed_share[suppressed_share > 0.5].index)]

    cycles = sorted(prepared['cycle'].unique())
    periods = prepared.drop_duplicates('cycle').set_index('cycle').loc[cycles, ['ref_start', 'ref_end']]
    industries = sorted(prepared['industry'].unique())

    # Same colors as the static figures.
    blue, gray, orange, ink = '#2a78d6', '#a3a29c', '#eb6834', '#52514e'
    summary_blues = {'Highest industry': '#104281', 'Median industry': '#2a78d6', 'Lowest industry': '#86b6ef'}

    def day(d):
        return f'{d:%b} {d.day}, {d.year}'

    def period_text(cycle):
        return f"{day(periods.loc[cycle, 'ref_start'])} to {day(periods.loc[cycle, 'ref_end'])}"

    def compute_views(selected, start_index, end_index):
        """Evidence tables behind the four figures for one selection of the controls."""
        window = cycles[start_index:end_index + 1]
        chosen = prepared[prepared['industry'].isin(selected) & prepared['cycle'].isin(window)]
        end_rows = chosen[chosen['cycle'].eq(window[-1])]
        latest = end_rows.dropna(subset=['ai_use_pct']).sort_values('ai_use_pct')
        by_cycle = chosen.pivot(index='ref_end', columns='industry', values='ai_use_pct')
        spread = pd.DataFrame({'Highest industry': by_cycle.max(axis=1),
                               'Median industry': by_cycle.median(axis=1),
                               'Lowest industry': by_cycle.min(axis=1)})
        k = min(3, len(window) // 2)
        first, last = window[:k], window[-k:]
        change = pd.DataFrame({
            'start_pct': chosen[chosen['cycle'].isin(first)].groupby('industry')['ai_use_pct'].mean(),
            'end_pct': chosen[chosen['cycle'].isin(last)].groupby('industry')['ai_use_pct'].mean(),
        }).dropna()
        change['change_points'] = change['end_pct'] - change['start_pct']
        change = change.sort_values('change_points')
        outlook = end_rows.dropna(subset=['ai_use_pct', 'expected_use_pct']).copy()
        outlook['expected_minus_current'] = outlook['expected_use_pct'] - outlook['ai_use_pct']
        outlook = outlook.sort_values('ai_use_pct')
        return {'window': window, 'latest': latest, 'by_cycle': by_cycle, 'spread': spread,
                'first': first, 'last': last, 'change': change, 'outlook': outlook,
                'suppressed_end': sorted(set(end_rows['industry']) - set(latest['industry']))}

    def style(fig, title, x_title, y_title='', rows=None):
        height = 460 if rows is None else max(320, 30 * rows + 150)
        fig.update_layout(template='plotly_white', height=height, title={'text': title, 'x': 0.01},
                          xaxis_title=x_title, yaxis_title=y_title, font={'family': 'Arial', 'size': 13},
                          margin={'l': 20, 'r': 30, 't': 70, 'b': 60}, hoverlabel={'bgcolor': 'white'})
        return fig

    def empty_figure(title):
        fig = go.Figure()
        fig.add_annotation(text='No industries selected. Choose at least one industry above.',
                           x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False, font={'size': 15})
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return style(fig, title, '')

    def latest_figure(v):
        t = v['latest']
        fig = go.Figure(go.Bar(
            x=t['ai_use_pct'], y=t['industry'], orientation='h', marker_color=blue,
            error_x={'type': 'data', 'array': 1.96 * t['ai_use_se'], 'color': ink, 'thickness': 1, 'width': 3},
            customdata=np.c_[1.96 * t['ai_use_se']],
            hovertemplate='%{y}<br>%{x:.1f}% of businesses used AI<br>95% interval: plus or minus %{customdata[0]:.1f} points<extra></extra>'))
        return style(fig, f"Businesses using AI by industry, {period_text(v['window'][-1])}",
                     'Businesses that used AI in the two weeks (% of businesses in the industry)', rows=len(t))

    def spread_figure(v):
        b, s = v['by_cycle'], v['spread']
        fig = go.Figure()
        for industry in b.columns:
            fig.add_trace(go.Scatter(x=b.index, y=b[industry], mode='lines', name=industry, showlegend=False,
                                     line={'color': '#d6d5d0', 'width': 1},
                                     hovertemplate=industry + '<br>%{x|%b %d, %Y}: %{y:.1f}%<extra></extra>'))
        for name, color in summary_blues.items():
            fig.add_trace(go.Scatter(x=s.index, y=s[name], mode='lines+markers', name=name,
                                     line={'color': color, 'width': 2.5}, marker={'size': 6},
                                     hovertemplate=name + '<br>%{x|%b %d, %Y}: %{y:.1f}%<extra></extra>'))
        fig = style(fig, 'AI use across the selected industries over time: highest, median, and lowest',
                    'End of the two-week reference period', 'Businesses that used AI (%)')
        fig.update_yaxes(rangemode='tozero')
        fig.update_layout(legend={'orientation': 'h', 'y': -0.2, 'x': 0})
        return fig

    def change_figure(v):
        c = v['change']
        fig = go.Figure()
        connector_x, connector_y = [], []
        for industry, row in c.iterrows():
            connector_x += [row['start_pct'], row['end_pct'], None]
            connector_y += [industry, industry, None]
        fig.add_trace(go.Scatter(x=connector_x, y=connector_y, mode='lines', line={'color': '#c3c2b7', 'width': 2},
                                 hoverinfo='skip', showlegend=False))
        start = f"First {len(v['first'])} cycles ({day(periods.loc[v['first'][0], 'ref_start'])} to {day(periods.loc[v['first'][-1], 'ref_end'])})"
        end = f"Last {len(v['last'])} cycles ({day(periods.loc[v['last'][0], 'ref_start'])} to {day(periods.loc[v['last'][-1], 'ref_end'])})"
        fig.add_trace(go.Scatter(x=c['start_pct'], y=c.index, mode='markers', name=start,
                                 marker={'color': gray, 'size': 10},
                                 hovertemplate='%{y}<br>Start average: %{x:.1f}%<extra></extra>'))
        fig.add_trace(go.Scatter(x=c['end_pct'], y=c.index, mode='markers+text', name=end,
                                 marker={'color': blue, 'size': 10},
                                 text=[f'{p:+.1f}' for p in c['change_points']], textposition='middle right',
                                 textfont={'color': ink, 'size': 11}, customdata=c[['change_points']],
                                 hovertemplate='%{y}<br>End average: %{x:.1f}%<br>Change: %{customdata[0]:+.1f} points<extra></extra>'))
        fig = style(fig, 'Change in AI use by industry (percentage points)',
                    'Businesses that used AI, average over the cycles (% of businesses in the industry)', rows=len(c))
        fig.update_yaxes(categoryorder='array', categoryarray=list(c.index))
        fig.update_xaxes(rangemode='tozero')
        fig.update_layout(legend={'orientation': 'h', 'y': -0.12 - 0.6 / max(len(c), 1), 'x': 0})
        return fig

    def outlook_figure(v):
        o = v['outlook']
        fig = go.Figure(go.Bar(
            x=o['expected_minus_current'], y=o['industry'], orientation='h', marker_color=orange,
            customdata=o[['ai_use_pct', 'expected_use_pct']],
            hovertemplate='%{y}<br>Current use: %{customdata[0]:.1f}%<br>Expected in six months: %{customdata[1]:.1f}%'
                          '<br>Difference: %{x:+.1f} points<extra></extra>'))
        fig.add_vline(x=0, line_color=ink, line_width=1)
        return style(fig, f"Expected AI use in the next six months minus current use, {period_text(v['window'][-1])}",
                     'Expected minus current use (percentage points). Ordered by current use, highest at top',
                     rows=len(o))

    def card(*children, **kwargs):
        return html.Div(className='dash-card', children=list(children), **kwargs)

    CONCLUSION = (
        'With all 17 industries and the full period selected, every industry used more AI at the end than at the '
        'start. Information, finance and insurance, and professional and technical services led at the start and '
        'gained the most, 9.5 to 10.7 points each, so the gap between the highest and lowest industry grew from '
        '29.5 to 36.2 points. Low-use industries grew faster compared with where they started. Construction almost '
        'doubled, from 8.5% to 16.8% of businesses. In the latest survey, expected use for the next six months is '
        'no more than 6.5 points above current use in any industry, and low-use industries do not expect bigger '
        'increases than high-use ones. The gap in points is growing, and businesses do not expect it to close soon.')
    LIMITATIONS = [
        'These are survey estimates of the share of businesses that used AI at all in a two-week period. They do '
        'not measure how much AI a business uses, how many of its workers use it, or whether it helps.',
        'Single two-week estimates move around, and the 95% intervals are wide for small industries such as '
        'utilities and mining. Census suppressed too many estimates for agriculture and for management of '
        'companies, so those two industries are left out. This file has the AI questions only from November 2025 '
        'on, so the comparable series covers about one year.',
    ]
    SOURCE = ('Source: U.S. Census Bureau, Business Trends and Outlook Survey (BTOS), sector file Sector.xlsx, '
              'https://www.census.gov/hfp/btos/data_downloads, accessed November 17, 2026. Question 7 (AI use in '
              'the last two weeks) and question 28 (expected AI use in the next six months), "Yes" answers, by '
              'two-digit NAICS sector. U.S. government data in the public domain.')

    marks = {i: f"{periods.loc[c, 'ref_end']:%b %Y}" for i, c in enumerate(cycles) if i % 4 == 0 or i == len(cycles) - 1}
    app = Dash(__name__)
    app.title = 'AI use by U.S. industry'
    app.layout = html.Div(className='dash-page', children=[
        card(html.H1('Which U.S. industries are adopting AI fastest?', style={'marginTop': '4px'}),
             html.P('For students, job seekers, and workforce planners who want to know where businesses are '
                    'already building AI into their work and whether the gap between industries is closing. '
                    'Data come from the Census Bureau survey that asks businesses every two weeks whether they '
                    'used AI.'),
             html.P('Census now words the question as "Super Intelligence or SI (formerly referred to as '
                    'Artificial Intelligence or AI)". This dashboard says AI.', style={'color': ink, 'fontSize': '14px'})),
        card(html.Label('Industries (updates all four figures)', htmlFor='industries', style={'fontWeight': 'bold'}),
             dcc.Dropdown(id='industries', options=industries, value=industries, multi=True,
                          placeholder='Select one or more industries'),
             html.Label('Survey period (updates all four figures)', htmlFor='cycle-range',
                        style={'fontWeight': 'bold', 'display': 'block', 'marginTop': '18px'}),
             dcc.RangeSlider(id='cycle-range', min=0, max=len(cycles) - 1, step=1, value=[0, len(cycles) - 1],
                             marks=marks, pushable=5, allowCross=False,
                             allow_direct_input=False),
             html.Button('Show all industries and the full period', id='reset', n_clicks=0,
                         style={'marginTop': '14px'}),
             html.P(id='selection-summary', style={'fontWeight': 'bold', 'marginTop': '14px', 'marginBottom': '4px'})),
        card(dcc.Graph(id='fig-latest')),
        card(dcc.Graph(id='fig-spread')),
        card(dcc.Graph(id='fig-change')),
        card(dcc.Graph(id='fig-outlook')),
        card(html.H2('Conclusion', style={'marginTop': '4px'}),
             html.P(id='conclusion-text', children=CONCLUSION)),
        card(html.H2('Limitations', style={'marginTop': '4px'}),
             html.Ul([html.Li(item) for item in LIMITATIONS])),
        card(html.P(SOURCE, style={'margin': '0', 'fontSize': '14px'})),
    ])

    @app.callback(Output('industries', 'value'), Output('cycle-range', 'value'), Input('reset', 'n_clicks'),
                  prevent_initial_call=True)
    def reset_controls(n_clicks):
        return industries, [0, len(cycles) - 1]

    @app.callback(Output('fig-latest', 'figure'), Output('fig-spread', 'figure'), Output('fig-change', 'figure'),
                  Output('fig-outlook', 'figure'), Output('selection-summary', 'children'),
                  Input('industries', 'value'), Input('cycle-range', 'value'))
    def update_dashboard(selected, cycle_range):
        selected = selected or []
        start_index, end_index = cycle_range
        window = cycles[start_index:end_index + 1]
        span = f"{day(periods.loc[window[0], 'ref_start'])} to {day(periods.loc[window[-1], 'ref_end'])}"
        if not selected:
            titles = ['Businesses using AI by industry', 'AI use over time',
                      'Change in AI use by industry', 'Expected AI use minus current use']
            message = (f'0 of {len(industries)} industries selected, so there is nothing to compare. '
                       f'Survey period: {span}.')
            return (*[empty_figure(t) for t in titles], message)
        v = compute_views(selected, start_index, end_index)
        message = (f"{len(selected)} of {len(industries)} industries selected. Survey period: {len(window)} two-week "
                   f"cycles, {span}. Figure 3 compares the average of the first {len(v['first'])} and last "
                   f"{len(v['last'])} cycles. Each value is the Census survey estimate of the percent of businesses "
                   f"in that industry. Industries shown in Figure 1: {len(v['latest'])}.")
        if v['suppressed_end']:
            message += (' Census suppressed the last-cycle estimate for ' + ', '.join(v['suppressed_end'])
                        + ', so it is left out of Figures 1 and 4.')
        return latest_figure(v), spread_figure(v), change_figure(v), outlook_figure(v), message

    app.compute_views = compute_views   # used by the notebook to check the dashboard values
    return app


data = pd.read_excel(Path(__file__).resolve().parent / 'data' / 'census_btos_sector_2026-11-17.xlsx',
                     sheet_name=None, dtype=str)
app = build_dashboard(data)
server = app.server

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8055, debug=False)
