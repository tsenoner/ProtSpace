import dash
from dash import html, dcc
import plotly.express as px
import pandas as pd

# Initialize the Dash app
app = dash.Dash(__name__)

# Sample data for the scatterplot
df = pd.DataFrame({
    'x': [1, 2, 3, 4],
    'y': [1, 4, 2, 3]
})

# Create the layout
app.layout = html.Div([
    html.H1('2D Scatterplot Visualization'),
    dcc.Graph(
        id='scatter-plot',
        figure=px.scatter(df, x='x', y='y', title='Sample Scatter Plot')
    )
])

if __name__ == '__main__':
    app.run_server(debug=False)