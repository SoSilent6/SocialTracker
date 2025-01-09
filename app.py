from flask import Flask, render_template
import pandas as pd
from datetime import datetime
import os
import math
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def show_excel():
    try:
        excel_path = 'Social Follower Count.xlsx'
        
        # Use logger instead of print
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Files in directory: {os.listdir()}")
        
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found at: {excel_path}")
            return f"Error: Data file not found at {excel_path}", 500
            
        # Get Excel file modification time
        mod_timestamp = os.path.getmtime(excel_path)
        current_time = datetime.now().timestamp()
        
        # Calculate time difference in minutes
        time_diff = (current_time - mod_timestamp) / 60
        
        # Format the time difference in Chinese
        if time_diff < 60:
            last_update = f"{math.floor(time_diff)}分钟前"
        else:
            hours = math.floor(time_diff / 60)
            last_update = f"{hours}小时前"

        # Read the Info sheet that has all the prepared data
        excel_file = pd.ExcelFile('Social Follower Count.xlsx')
        info_sheet = pd.read_excel(excel_file, 'Info', engine='openpyxl', dtype=object)
        
        # Function to convert zeros to empty string
        def convert_zero_to_empty(value):
            try:
                float_val = float(value)
                return "" if float_val == 0 else value
            except:
                return value

        # First define the column names as variables so they stay consistent
        columns = {
            'token': "代币",
            'volume': "24h交易量 <button class='sort-arrow'>↕</button>",
            'x_followers': "X粉丝数量",
            'x_24h': "24h粉丝涨跌(X) <button class='sort-arrow'>↕</button>",
            'x_3d': "3天粉丝涨跌(X) <button class='sort-arrow'>↕</button>",
            'discord_followers': "Discord粉丝数量",
            'discord_24h': "24h粉丝涨跌(Discord) <button class='sort-arrow'>↕</button>",
            'discord_3d': "3天粉丝涨跌(Discord) <button class='sort-arrow'>↕</button>"
        }

        # Create DataFrame with correct column order
        result_df = pd.DataFrame({
            columns['token']: info_sheet['Token'],
            columns['volume']: info_sheet['24h交易量'].fillna("").apply(convert_zero_to_empty),
            columns['x_followers']: info_sheet['X粉丝数量'].fillna("").apply(
                lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) and float(x) != 0 else ""),
            columns['x_24h']: info_sheet['24h粉丝涨跌(X)'].fillna("").apply(convert_zero_to_empty),
            columns['x_3d']: info_sheet['3天粉丝涨跌(X)'].fillna("").apply(convert_zero_to_empty),
            columns['discord_followers']: info_sheet['Discord粉丝数量'].fillna("").apply(
                lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) and float(x) != 0 else ""),
            columns['discord_24h']: info_sheet['24h粉丝涨跌(Discord)'].fillna("").apply(convert_zero_to_empty),
            columns['discord_3d']: info_sheet['3天粉丝涨跌(Discord)'].fillna("").apply(convert_zero_to_empty)
        })

        def color_percentage(value):
            if isinstance(value, (str, float)) and value != "":
                try:
                    val = float(str(value).replace('%', '')) if isinstance(value, str) else float(value)
                    if val < 0:
                        return 'color: rgb(255, 68, 68)'  # Bright red
                    elif val > 0:
                        return 'color: rgb(68, 255, 68)'  # Bright green
                except:
                    pass
            return ''

        def format_token_column(value):
            return f'<div style="display: flex; justify-content: space-between; align-items: center;">{value} <a href="/token/{value}" class="token-link">更多数据</a></div>'

        styled_df = result_df.style\
            .hide(axis='index')\
            .map(color_percentage, subset=[
                columns['volume'],
                columns['x_24h'],
                columns['x_3d'],
                columns['discord_24h'],
                columns['discord_3d']
            ])\
            .format({
                columns['token']: format_token_column,
                columns['x_followers']: lambda x: "{:,}".format(x) if isinstance(x, (int, float)) and x != "" else x,
                columns['discord_followers']: lambda x: "{:,}".format(x) if isinstance(x, (int, float)) and x != "" else x,
                columns['volume']: lambda x: f"{x}%" if x != "" else x,
                columns['x_24h']: lambda x: f"{x}%" if x != "" else x,
                columns['x_3d']: lambda x: f"{x}%" if x != "" else x,
                columns['discord_24h']: lambda x: f"{x}%" if x != "" else x,
                columns['discord_3d']: lambda x: f"{x}%" if x != "" else x
            })\
            .set_table_attributes('border="0" class="dataframe table table-dark table-striped" style="font-weight: normal"')\
            .set_table_styles([
                {'selector': 'th', 'props': [('font-weight', 'normal')]},
                {'selector': 'td', 'props': [('font-weight', 'normal')]}
            ])

        html_table = styled_df.to_html(escape=False)
        
        return render_template('index.html', data=html_table, last_update=last_update)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}", 500

@app.route('/token/<token_name>')
def token_page(token_name):
    # Read the Excel file
    excel_file = pd.ExcelFile('Social Follower Count.xlsx')
    x_sheet = pd.read_excel(excel_file, 'X')
    discord_sheet = pd.read_excel(excel_file, 'Discord')
    
    # Find the rows for this token in both sheets
    x_row = x_sheet[x_sheet.iloc[:, 0] == token_name].iloc[0]
    discord_row = discord_sheet[discord_sheet.iloc[:, 0] == token_name].iloc[0]
    
    # Get X history data
    x_history = []
    col_index = 10  # Starting at column K (index 10)
    
    while col_index < len(x_row):
        try:
            time = x_row[col_index]  # Time column (K, M, O, Q...)
            followers = x_row[col_index + 1]  # Followers column (L, N, P, R...)
            
            if pd.notna(time) and pd.notna(followers):
                x_history.append({
                    'time': time,
                    'followers': int(followers)
                })
            
            col_index += 2  # Move to next pair of columns
        except:
            break
    
    # Get Discord history data
    discord_history = []
    col_index = 10  # Starting at column K (index 10)
    
    while col_index < len(discord_row):
        try:
            time = discord_row[col_index]  # Time column (K, M, O, Q...)
            followers = discord_row[col_index + 1]  # Followers column (L, N, P, R...)
            
            if pd.notna(time) and pd.notna(followers):
                discord_history.append({
                    'time': time,
                    'followers': int(followers)
                })
            
            col_index += 2  # Move to next pair of columns
        except:
            break
    
    # Sort by time (newest first)
    x_history.sort(key=lambda x: x['time'], reverse=True)
    discord_history.sort(key=lambda x: x['time'], reverse=True)
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{token_name} 更多数据</title>
        <style>
            body {{
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }}
            
            .back-button {{
                color: #00ffcc;
                text-decoration: none;
                padding: 8px 16px;
                border: 1px solid #00ffcc;
                border-radius: 4px;
                margin-bottom: 20px;
                display: inline-block;
            }}
            
            .back-button:hover {{
                background: #00ffcc22;
            }}
            
            .tabs {{
                display: flex;
                gap: 1px;
                margin: 20px 0;
                border-bottom: 1px solid #00ffcc;
            }}
            
            .tab {{
                padding: 10px 20px;
                cursor: pointer;
                color: #00ffcc;
                border: 1px solid #00ffcc;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background: black;
            }}
            
            .tab.active {{
                background: #00ffcc22;
            }}
            
            .content {{
                display: none;
            }}
            
            .content.active {{
                display: block;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #333;
            }}
            
            th {{
                color: #00ffcc;
            }}
            
            .followers {{
                text-align: right;
            }}
        </style>
    </head>
    <body>
        <a href="/" class="back-button">← 上一页</a>
        <h1 style="color: #00ffcc;">{token_name}</h1>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('x')">X数据</div>
            <div class="tab" onclick="switchTab('discord')">Discord数据</div>
        </div>
        
        <div id="x" class="content active">
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th style="text-align: right">粉丝数</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f"""
                        <tr>
                            <td>{entry['time']}</td>
                            <td class="followers">{'{:,}'.format(entry['followers'])}</td>
                        </tr>
                    """ for entry in x_history)}
                </tbody>
            </table>
        </div>
        
        <div id="discord" class="content">
            <table>
                <thead>
                    <tr>
                        <th>时间</th>
                        <th style="text-align: right">粉丝数</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f"""
                        <tr>
                            <td>{entry['time']}</td>
                            <td class="followers">{'{:,}'.format(entry['followers'])}</td>
                        </tr>
                    """ for entry in discord_history)}
                </tbody>
            </table>
        </div>
        
        <script>
            function switchTab(tab) {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
                
                document.querySelector(`.tab:nth-child(${{tab === 'x' ? 1 : 2}})`).classList.add('active');
                document.getElementById(tab).classList.add('active');
            }}
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
   app.run(host='0.0.0.0')