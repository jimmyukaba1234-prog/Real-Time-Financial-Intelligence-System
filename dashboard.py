"""
Dash Dashboard for Financial Analytics
Alternative to Streamlit with more customization options
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scraper import FinancialScraper
from datetime import datetime, timedelta
import sqlite3
import warnings
warnings.filterwarnings('ignore')

# Initialize Dash app with Bootstrap
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "Financial Analytics Dashboard"

# Database connection
DB_PATH = 'financial_data.db'

def get_db_connection():
    """Create database connection"""
    return sqlite3.connect(DB_PATH)

def get_tickers():
    """Get list of available tickers"""
    conn = get_db_connection()
    query = "SELECT DISTINCT Ticker FROM stock_prices ORDER BY Ticker"
    tickers = pd.read_sql_query(query, conn)['Ticker'].tolist()
    conn.close()
    return tickers

def get_stock_data(ticker, start_date=None, end_date=None):
    """Get stock data for specific ticker"""
    conn = get_db_connection()
    
    if start_date and end_date:
        query = """
        SELECT * FROM stock_prices 
        WHERE Ticker = ? AND Date BETWEEN ? AND ?
        ORDER BY Date
        """
        params = (ticker, start_date, end_date)
    else:
        query = "SELECT * FROM stock_prices WHERE Ticker = ? ORDER BY Date"
        params = (ticker,)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_latest_data():
    """Get latest data for all tickers"""
    conn = get_db_connection()
    query = """
    SELECT sp1.* 
    FROM stock_prices sp1
    INNER JOIN (
        SELECT Ticker, MAX(Date) as LatestDate
        FROM stock_prices
        GROUP BY Ticker
    ) sp2 ON sp1.Ticker = sp2.Ticker AND sp1.Date = sp2.LatestDate
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calculate_metrics():
    """Calculate key financial metrics"""
    conn = get_db_connection()
    
    try:
        # Overall metrics
        overall_query = """
        SELECT 
            COUNT(DISTINCT Ticker) as Total_Tickers,
            COUNT(*) as Total_Records,
            MIN(Date) as Earliest_Date,
            MAX(Date) as Latest_Date,
            AVG(Daily_Return) * 100 as Avg_Daily_Return,
            AVG(Volume) as Avg_Volume
        FROM stock_prices
        """
        overall_df = pd.read_sql_query(overall_query, conn)
        
        # If no data, return empty
        if overall_df.empty or overall_df['Total_Records'].iloc[0] == 0:
            return pd.DataFrame({
                'Total_Tickers': [0],
                'Total_Records': [0],
                'Earliest_Date': [''],
                'Latest_Date': [''],
                'Avg_Daily_Return': [0],
                'Avg_Volume': [0]
            }), pd.DataFrame()
        
        # Get all data and calculate in pandas
        all_data = pd.read_sql_query("SELECT * FROM stock_prices", conn)
        
        # Calculate metrics per ticker using pandas (not SQL)
        metrics = []
        for ticker in all_data['Ticker'].unique():
            ticker_data = all_data[all_data['Ticker'] == ticker]
            
            if len(ticker_data) > 0:
                metrics.append({
                    'Ticker': ticker,
                    'Records': len(ticker_data),
                    'Avg_Return': ticker_data['Daily_Return'].mean() * 100 if len(ticker_data) > 0 else 0,
                    'Volatility': ticker_data['Daily_Return'].std() * 100 if len(ticker_data) > 1 else 0,
                    'Period_High': ticker_data['High'].max(),
                    'Period_Low': ticker_data['Low'].min(),
                    'Avg_Volume': ticker_data['Volume'].mean()
                })
        
        ticker_df = pd.DataFrame(metrics)
        ticker_df = ticker_df.sort_values('Avg_Return', ascending=False)
        
        return overall_df, ticker_df
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        # Return empty dataframes on error
        return pd.DataFrame({
            'Total_Tickers': [0],
            'Total_Records': [0],
            'Earliest_Date': [''],
            'Latest_Date': [''],
            'Avg_Daily_Return': [0],
            'Avg_Volume': [0]
        }), pd.DataFrame()
    finally:
        conn.close()

# Initialize data
tickers = get_tickers()
latest_data = get_latest_data()
overall_metrics, ticker_metrics = calculate_metrics()

# Define app layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("📊 Financial Analytics Dashboard", 
                   className="text-center my-4"),
            html.P("Interactive dashboard for financial data analysis and visualization",
                  className="text-center text-muted")
        ])
    ]),
    
    # Top Metrics Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📈 Total Tickers", className="card-title"),
                    html.H3(f"{overall_metrics['Total_Tickers'].iloc[0]}", 
                           className="card-text text-primary")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Total Records", className="card-title"),
                    html.H3(f"{overall_metrics['Total_Records'].iloc[0]:,}", 
                           className="card-text text-success")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📅 Data Period", className="card-title"),
                    html.H3(f"{overall_metrics['Earliest_Date'].iloc[0][:10]} to {overall_metrics['Latest_Date'].iloc[0][:10]}", 
                           className="card-text text-info")
                ])
            ], className="mb-3")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("💰 Avg Daily Return", className="card-title"),
                    html.H3(f"{overall_metrics['Avg_Daily_Return'].iloc[0]:.2f}%", 
                           className="card-text text-warning")
                ])
            ], className="mb-3")
        ], width=3),
    ], className="mb-4"),
    
    # Add this to your layout after the metrics cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("⚡ Live Market Data", className="card-title"),
                    html.Div(id='live-quotes'),
                    dcc.Interval(
                        id='interval-component',
                        interval=30*1000,  # in milliseconds (30 seconds)
                        n_intervals=0
                    )
                ])
            ], className="mb-3")
        ])
    ], className="mb-4"),
    
    # Control Panel
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("⚙️ Control Panel", className="card-title mb-3"),
                    
                    # Ticker Selection
                    html.Label("Select Ticker(s):"),
                    dcc.Dropdown(
                        id='ticker-dropdown',
                        options=[{'label': t, 'value': t} for t in tickers],
                        value=tickers[:1] if tickers else [],
                        multi=True,
                        placeholder="Select ticker(s)...",
                        className="mb-3"
                    ),
                    
                    # Date Range
                    html.Label("Date Range:"),
                    dcc.DatePickerRange(
                        id='date-picker',
                        start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d'),
                        display_format='YYYY-MM-DD',
                        className="mb-3"
                    ),
                    
                    # Analysis Type
                    html.Label("Analysis Type:"),
                    dcc.Dropdown(
                        id='analysis-type',
                        options=[
                            {'label': '📈 Price Trends', 'value': 'price'},
                            {'label': '📊 Technical Indicators', 'value': 'technical'},
                            {'label': '📉 Returns Analysis', 'value': 'returns'},
                            {'label': '📋 Portfolio View', 'value': 'portfolio'},
                            {'label': '📊 Volume Analysis', 'value': 'volume'}
                        ],
                        value='price',
                        className="mb-3"
                    ),
                    
                    # Update Button
                    dbc.Button("🔄 Update Dashboard", 
                              id='update-button',
                              color="primary",
                              className="w-100")
                ])
            ])
        ], width=3),
        
        # Main Content Area
        dbc.Col([
            # Tabbed Content
            dbc.Tabs([
                # Chart Tab
                dbc.Tab([
                    dcc.Loading(
                        id="loading-charts",
                        type="circle",
                        children=[
                            dcc.Graph(id='main-chart', className="mt-3"),
                            dcc.Graph(id='secondary-chart', className="mt-3")
                        ]
                    )
                ], label="📈 Charts", tab_id="charts"),
                
                # Data Tab
                dbc.Tab([
                    dcc.Loading(
                        id="loading-data",
                        type="circle",
                        children=[
                            dash_table.DataTable(
                                id='data-table',
                                columns=[],
                                data=[],
                                page_size=10,
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px'
                                },
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'fontWeight': 'bold'
                                }
                            ),
                            dbc.Button("📥 Download CSV", 
                                      id='download-button',
                                      color="success",
                                      className="mt-3"),
                            dcc.Download(id="download-data")
                        ]
                    )
                ], label="📋 Data", tab_id="data"),
                
                # Metrics Tab
                dbc.Tab([
                    dcc.Loading(
                        id="loading-metrics",
                        type="circle",
                        children=[
                            html.H5("📊 Performance Metrics", className="mt-3"),
                            dash_table.DataTable(
                                id='metrics-table',
                                columns=[
                                    {'name': 'Ticker', 'id': 'Ticker'},
                                    {'name': 'Avg Return (%)', 'id': 'Avg_Return'},
                                    {'name': 'Volatility (%)', 'id': 'Volatility'},
                                    {'name': 'Period High', 'id': 'Period_High'},
                                    {'name': 'Period Low', 'id': 'Period_Low'},
                                    {'name': 'Avg Volume', 'id': 'Avg_Volume'}
                                ],
                                data=ticker_metrics.to_dict('records'),
                                page_size=10,
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px'
                                },
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'fontWeight': 'bold'
                                }
                            )
                        ]
                    )
                ], label="📊 Metrics", tab_id="metrics"),
                
                # Correlation Tab
                dbc.Tab([
                    dcc.Loading(
                        id="loading-correlation",
                        type="circle",
                        children=[
                            html.H5("🔗 Correlation Matrix", className="mt-3"),
                            dcc.Graph(id='correlation-heatmap'),
                            html.H5("📊 Scatter Matrix", className="mt-4"),
                            dcc.Graph(id='scatter-matrix')
                        ]
                    )
                ], label="🔗 Correlation", tab_id="correlation")
            ], id="tabs", active_tab="charts")
        ], width=9)
    ]),
    
    # Hidden div for storing intermediate values
    dcc.Store(id='data-store'),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P("Financial Analytics Dashboard • Last Updated: " + 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  className="text-center text-muted small")
        ])
    ], className="mt-4")
], fluid=True)

# Callbacks for interactivity
@app.callback(
    [Output('main-chart', 'figure'),
     Output('secondary-chart', 'figure'),
     Output('data-table', 'columns'),
     Output('data-table', 'data'),
     Output('data-store', 'data')],
    [Input('update-button', 'n_clicks'),
     Input('tabs', 'active_tab')],
    [State('ticker-dropdown', 'value'),
     State('date-picker', 'start_date'),
     State('date-picker', 'end_date'),
     State('analysis-type', 'value')]
)
def update_dashboard(n_clicks, active_tab, selected_tickers, start_date, end_date, analysis_type):
    """Update dashboard based on user inputs"""
    
    if not selected_tickers:
        selected_tickers = tickers[:1] if tickers else []
    
    # Get data for selected tickers
    all_data = {}
    combined_data = []
    
    for ticker in selected_tickers:
        df = get_stock_data(ticker, start_date, end_date)
        if not df.empty:
            all_data[ticker] = df
            df_copy = df.copy()
            df_copy['Ticker'] = ticker
            combined_data.append(df_copy)
    
    if not all_data:
        # Return empty figures if no data
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No data available for selected criteria",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        
        empty_table = pd.DataFrame()
        
        return empty_fig, empty_fig, [], [], {}
    
    # Combine all data
    if combined_data:
        combined_df = pd.concat(combined_data, ignore_index=True)
    else:
        combined_df = pd.DataFrame()
    
    # Create main chart based on analysis type
    main_fig = create_main_chart(all_data, analysis_type)
    
    # Create secondary chart
    secondary_fig = create_secondary_chart(all_data, analysis_type)
    
    # Prepare data table
    table_columns = [{'name': col, 'id': col} for col in combined_df.columns]
    table_data = combined_df.to_dict('records')
    
    # Store data for download
    store_data = combined_df.to_dict('records') if not combined_df.empty else {}
    
    return main_fig, secondary_fig, table_columns, table_data, store_data

@app.callback(
    Output('live-quotes', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('ticker-dropdown', 'value')]
)
def update_live_quotes(n_intervals, selected_tickers):
    """Update live quotes"""
    if not selected_tickers:
        return "Select tickers to see live data"
    
    try:
        # Ensure selected_tickers is a list
        if isinstance(selected_tickers, str):
            tickers_list = [selected_tickers]
        else:
            tickers_list = selected_tickers
        
        # Limit to 3 tickers for performance
        display_tickers = tickers_list[:3]
        
        scraper = FinancialScraper()
        realtime_data = scraper.get_realtime_tickers_data(display_tickers)
        
        quotes = []
        for ticker in display_tickers:
            if ticker in realtime_data and 'error' not in realtime_data[ticker]:
                data = realtime_data[ticker]
                
                # Calculate color based on change
                change_color = 'green' if data.get('close', 0) >= data.get('open', 0) else 'red'
                
                quotes.append(
                    dbc.Row([
                        dbc.Col(html.Strong(ticker), width=2),
                        dbc.Col(html.Span(f"${data.get('close', 0):.2f}", 
                                style={'color': change_color, 'fontWeight': 'bold'}), width=3),
                        dbc.Col(html.Small(f"Vol: {data.get('volume', 0):,}"), width=4),
                        dbc.Col(html.Small(data.get('last_updated', '')[:16]), width=3)
                    ], className="mb-2")
                )
        
        return quotes if quotes else "No live data available"
        
    except Exception as e:
        return f"Error loading live data: {str(e)[:50]}"

def create_main_chart(data_dict, analysis_type):
    """Create main chart based on analysis type"""
    
    if analysis_type == 'price':
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price Movement', 'Volume'),
            row_heights=[0.7, 0.3]
        )
        
        for ticker, df in data_dict.items():
            # Price chart
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=ticker,
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # Volume chart
            colors = ['red' if row['Close'] < row['Open'] else 'green' 
                     for _, row in df.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name=f"{ticker} Volume",
                    marker_color=colors,
                    showlegend=False,
                    opacity=0.5
                ),
                row=2, col=1
            )
        
        fig.update_layout(
            height=600,
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            title_text="Price and Volume Analysis"
        )
    
    elif analysis_type == 'technical':
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price with MAs', 'RSI', 'Daily Returns'),
            row_heights=[0.4, 0.3, 0.3]
        )
        
        for ticker, df in data_dict.items():
            # Price with Moving Averages
            fig.add_trace(
                go.Scatter(x=df['Date'], y=df['Close'], 
                          name=f'{ticker} Close', 
                          mode='lines',
                          line=dict(width=2)),
                row=1, col=1
            )
            
            if 'SMA_20' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['Date'], y=df['SMA_20'], 
                              name=f'{ticker} SMA 20',
                              mode='lines',
                              line=dict(dash='dash', width=1)),
                    row=1, col=1
                )
            
            if 'SMA_50' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['Date'], y=df['SMA_50'], 
                              name=f'{ticker} SMA 50',
                              mode='lines',
                              line=dict(dash='dot', width=1)),
                    row=1, col=1
                )
            
            # RSI
            if 'RSI' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['Date'], y=df['RSI'], 
                              name=f'{ticker} RSI',
                              mode='lines'),
                    row=2, col=1
                )
            
            # Daily Returns
            if 'Daily_Return' in df.columns:
                colors = ['green' if x >= 0 else 'red' for x in df['Daily_Return']]
                fig.add_trace(
                    go.Bar(x=df['Date'], y=df['Daily_Return']*100, 
                          name=f'{ticker} Returns',
                          marker_color=colors),
                    row=3, col=1
                )
        
        # Add RSI reference lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                     opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", 
                     opacity=0.5, row=2, col=1)
        
        fig.update_layout(
            height=700,
            template='plotly_white',
            title_text="Technical Indicators"
        )
    
    elif analysis_type == 'returns':
        fig = go.Figure()
        
        for ticker, df in data_dict.items():
            if 'Cumulative_Return' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df['Date'], 
                              y=df['Cumulative_Return']*100,
                              name=ticker,
                              mode='lines+markers',
                              line=dict(width=2))
                )
        
        fig.update_layout(
            height=500,
            template='plotly_white',
            title_text="Cumulative Returns (%)",
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            hovermode='x unified'
        )
    
    elif analysis_type == 'portfolio':
        # Create pie chart of current allocations
        latest_prices = get_latest_data()
        portfolio_df = latest_prices[latest_prices['Ticker'].isin(list(data_dict.keys()))]
        
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{'type': 'pie'}, {'type': 'bar'}]],
            subplot_titles=('Portfolio Allocation', 'Performance Comparison')
        )
        
        # Pie chart
        fig.add_trace(
            go.Pie(
                labels=portfolio_df['Ticker'],
                values=portfolio_df['Close'],
                hole=0.3,
                textinfo='label+percent'
            ),
            row=1, col=1
        )
        
        # Bar chart
        for ticker, df in data_dict.items():
            if not df.empty:
                total_return = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / 
                               df['Close'].iloc[0] * 100)
                fig.add_trace(
                    go.Bar(
                        x=[ticker],
                        y=[total_return],
                        name=ticker,
                        text=f"{total_return:.1f}%",
                        textposition='auto'
                    ),
                    row=1, col=2
                )
        
        fig.update_layout(
            height=500,
            template='plotly_white',
            title_text="Portfolio Analysis"
        )
    
    else:  # volume analysis
        fig = go.Figure()
        
        for ticker, df in data_dict.items():
            fig.add_trace(
                go.Scatter(x=df['Date'], y=df['Volume'],
                          name=ticker,
                          mode='lines',
                          line=dict(width=1),
                          opacity=0.7)
            )
        
        fig.update_layout(
            height=500,
            template='plotly_white',
            title_text="Volume Analysis",
            xaxis_title="Date",
            yaxis_title="Volume",
            hovermode='x unified'
        )
    
    return fig

def create_secondary_chart(data_dict, analysis_type):
    """Create secondary chart"""
    
    if len(data_dict) > 1:
        # Compare closing prices
        fig = go.Figure()
        
        for ticker, df in data_dict.items():
            # Normalize prices for comparison
            if not df.empty:
                normalized_price = df['Close'] / df['Close'].iloc[0] * 100
                fig.add_trace(
                    go.Scatter(x=df['Date'], y=normalized_price,
                              name=ticker,
                              mode='lines',
                              line=dict(width=2))
                )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            title_text="Normalized Price Comparison (Base=100)",
            xaxis_title="Date",
            yaxis_title="Normalized Price",
            hovermode='x unified'
        )
    else:
        # Show volatility or other single-stock analysis
        fig = go.Figure()
        
        for ticker, df in data_dict.items():
            if 'Daily_Return' in df.columns:
                # Histogram of returns
                fig.add_trace(
                    go.Histogram(
                        x=df['Daily_Return']*100,
                        name=ticker,
                        nbinsx=30,
                        opacity=0.7
                    )
                )
        
        fig.update_layout(
            height=400,
            template='plotly_white',
            title_text="Returns Distribution",
            xaxis_title="Daily Return (%)",
            yaxis_title="Frequency",
            bargap=0.1
        )
    
    return fig

@app.callback(
    [Output('correlation-heatmap', 'figure'),
     Output('scatter-matrix', 'figure')],
    [Input('ticker-dropdown', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_correlation_analysis(selected_tickers, start_date, end_date):
    """Update correlation analysis"""
    
    if not selected_tickers or len(selected_tickers) < 2:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Select at least 2 tickers for correlation analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, empty_fig
    
    # Get data and create correlation matrix
    price_data = {}
    
    for ticker in selected_tickers:
        df = get_stock_data(ticker, start_date, end_date)
        if not df.empty:
            price_data[ticker] = df.set_index('Date')['Close']
    
    if len(price_data) < 2:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Insufficient data for correlation analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, empty_fig
    
    # Create DataFrame
    combined = pd.DataFrame(price_data)
    
    # Calculate returns
    returns = combined.pct_change().dropna()
    
    # Correlation matrix heatmap
    corr_matrix = returns.corr()
    
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        text=corr_matrix.round(2).values,
        texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    heatmap_fig.update_layout(
        title="Correlation Matrix of Returns",
        height=500,
        template='plotly_white'
    )
    
    # Scatter matrix
    if len(returns.columns) <= 5:  # Limit to 5 for performance
        scatter_fig = px.scatter_matrix(
            returns,
            dimensions=returns.columns,
            title="Scatter Matrix of Returns"
        )
        scatter_fig.update_layout(height=600)
    else:
        # If too many tickers, show sample
        scatter_fig = px.scatter(
            returns,
            x=returns.columns[0],
            y=returns.columns[1],
            title=f"Scatter Plot: {returns.columns[0]} vs {returns.columns[1]}"
        )
        scatter_fig.update_layout(height=500)
    
    return heatmap_fig, scatter_fig

@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("data-store", "data"),
    prevent_initial_call=True
)
def download_data(n_clicks, stored_data):
    """Download data as CSV"""
    if stored_data:
        df = pd.DataFrame(stored_data)
        return dcc.send_data_frame(df.to_csv, "financial_data.csv")
    return None

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)