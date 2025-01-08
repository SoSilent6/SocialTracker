from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def show_excel():
   # Read both sheets from the single Excel file
   excel_file = pd.ExcelFile('Social Follower Count.xlsx')
   x_sheet = pd.read_excel(excel_file, 'X')
   discord_sheet = pd.read_excel(excel_file, 'Discord')
   
   x_sheet.columns = x_sheet.columns.str.strip()
   discord_sheet.columns = discord_sheet.columns.str.strip()

   def color_percentage(value):
       if isinstance(value, (str, float)) and value != "":
           try:
               # If it's a string, remove the % sign first
               val = float(str(value).replace('%', '')) if isinstance(value, str) else float(value)
               if val < 0:
                   return 'color: rgb(255, 68, 68)'  # Bright red
               elif val > 0:
                   return 'color: rgb(68, 255, 68)'  # Bright green
           except:
               pass
       return ''

   def format_token_column(value):
       return f'{value} <a href="/token/{value}" class="token-link">更多数据</a>'

   result_df = pd.DataFrame({
       "代币": x_sheet.iloc[:, 0],
       "24h交易量": x_sheet.iloc[:, 1].fillna(""),
       "X粉丝数量": x_sheet.iloc[:, 11].fillna("").apply(
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "24h粉丝涨跌 (X)": x_sheet.iloc[:, 1].fillna(""),
       "Discord粉丝数量": discord_sheet.iloc[:, 11].fillna("").apply(
           lambda x: int(x) if isinstance(x, (int, float)) and not pd.isna(x) else x),
       "24h粉丝涨跌 (Discord)": discord_sheet.iloc[:, 1].fillna("")
   })

   styled_df = result_df.style\
       .hide(axis='index')\
       .applymap(color_percentage, subset=['24h交易量', '24h粉丝涨跌 (X)', '24h粉丝涨跌 (Discord)'])\
       .set_table_attributes('border="0" class="dataframe table table-dark table-striped" style="font-weight: normal"')\
       .set_table_styles([
           {'selector': 'th', 'props': [('font-weight', 'normal')]},
           {'selector': 'td', 'props': [('font-weight', 'normal')]}
       ])\
       .format({
           "代币": format_token_column,
           "X粉丝数量": lambda x: "{:,}".format(x) if isinstance(x, (int, float)) else x,
           "Discord粉丝数量": lambda x: "{:,}".format(x) if isinstance(x, (int, float)) else x,
           "24h交易量": lambda x: f"{x}%" if x != "" else x,
           "24h粉丝涨跌 (X)": lambda x: f"{x}%" if x != "" else x,
           "24h粉丝涨跌 (Discord)": lambda x: f"{x}%" if x != "" else x
       })

   html_table = styled_df.to_html()
   
   # Write to both locations - with explicit UTF-8 encoding
   with open("templates/index.html", "r", encoding='utf-8') as template_file:
       template_content = template_file.read()
   
   final_html = template_content.replace("{{ data | safe }}", html_table)
   
   # Write to root directory for Netlify - with explicit UTF-8 encoding
   with open("index.html", "w", encoding='utf-8') as f:
       f.write(final_html)
   
   # Return for Flask local development
   return render_template('index.html', data=html_table)

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
   app.run(debug=True)