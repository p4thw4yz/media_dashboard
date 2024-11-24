from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import requests
import plotly.graph_objs as go
from collections import deque
import dash_bootstrap_components as dbc

class MediaDashboard:
    def __init__(self):
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Media Dash/Monitor"
        self.server = self.app.server

        # API Configuration
        self.SONARR_API = "http://localhost:8989/api/v3"
        self.SONARR_KEY = "API_KEY"

        self.RADARR_API = "http://localhost:7878/api/v3"
        self.RADARR_KEY = "API_KEY"

        self.QBITTORRENT_API = "http://localhost:8080/api/v2"
        self.QBITTORRENT_USERNAME = "username"
        self.QBITTORRENT_PASSWORD = "password"

        self.download_speeds = deque(maxlen=50) 
        self.upload_speeds = deque(maxlen=50)

        self.layout()
        self.callbacks()

    def layout(self):
        """Define the dashboard layout."""
        self.app.layout = html.Div([
            html.Div([
                # Header Section
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'width': '100%'}),  # Flexbox for alignment
                html.H1(self.app.title, style={
                    'color': '#FFFFFF',
                    'fontWeight': 'bold', 'fontFamily': 'Inter, sans-serif',
                    'fontSize': '2.5rem', 'marginBottom': '20px',
                    'textShadow': '0px 4px 10px rgba(255, 255, 255, 0.5)',
                    'flexGrow': 1, 
                    'textAlign': 'center'
                }),

                # Graph for Speeds
                html.Div([
                    dcc.Graph(id="speed-graph", style=self.graph_container_style())
                ], style={'marginBottom': '30px'}),
                
                # Card Container
                html.Div([
                    html.Div(self._create_card("Sonarr Activities", "sonarr-activities", title_color='darkcyan'), style={'flex': '1'}),
                    html.Div(self._create_card("Radarr Activities", "radarr-activities", title_color='orange'), style={'flex': '1', 'marginLeft': '10px'}),
                    html.Div(self._create_card("qBittorrent Activities", "qbittorrent-activities"), style={'flex': '1', 'marginLeft': '10px'}),
                ], style={'display': 'flex', 'marginBottom': '20px', 'gap': '20px'}),

                # Footer
                html.Div("Dashboard by p4thw4yz", style={
                    'textAlign': 'center', 
                    'color': '#AAAAAA', 
                    'marginTop': '20px',
                    'fontSize': '0.9rem'
                }),

                # Update Intervals
                dcc.Interval(id="update-interval", interval=10000, n_intervals=0)  # Update every 10 seconds
            ], style={
                'background': 'radial-gradient(circle at 50% 50%, #0f0f0f, #1c1c1c 80%)',
                'padding': '20px',
                'minHeight': '100vh',
                'color': '#FFFFFF',
                'fontFamily': 'Inter, sans-serif'
            })
        ])

    def graph_container_style(self):
        """Style for the graph container."""
        return {
            'marginTop': '20px', 
            'backgroundColor': 'rgba(0, 0, 0, 0.0)',  # Changed to transparent
            'padding': '20px', 
            'borderRadius': '15px', 
            'boxShadow': '0 8px 30px rgba(0, 0, 0, 0.5)'  # Unchanged
        }

    def _create_card(self, title, id_name, title_color='white'):
        """Create a card with a title and a content area."""
        return html.Div([
            html.Div(title, style={**self.card_title_style(), 'color': title_color}),
            html.Div(id=id_name, style=self.card_style())
        ], style=self.card_style())

    def card_style(self):
        """Style for the card."""
        return {
            'backgroundColor': 'rgba(0, 0, 0, 0.0)',  # Changed to transparent
            'padding': '15px',
            'borderRadius': '15px',
            'boxShadow': '0 8px 30px rgba(0, 0, 0, 0.5)',  # Unchanged
            'color': '#FFFFFF',
            'flex': '1'
        }

    def card_title_style(self):
        """Style for the card title."""
        return {
            'fontWeight': 'bold', 
            'fontSize': '1.2rem', 
            'marginBottom': '10px',
            'color': '#66CCFF'  # Keep title color for contrast
        }
    
    def data_box_style_green(self):
        """Style for data boxes with a green tinge."""
        return {
            'backgroundColor': 'rgba(0, 255, 0, 0.05)',  # More transparent light green tinge
            'padding': '15px',
            'borderRadius': '15px',
            'boxShadow': '0 8px 30px rgba(0, 0, 0, 0.5)',  # Unchanged
            'color': '#FFFFFF',
            'flex': '1',
            'border': '1px solid rgba(255, 255, 255, 0.5)'  # Light grey border
        }
        
    def data_box_style(self):
        """Style for data boxes."""
        return {
            'backgroundColor': 'rgba(0, 0, 0, 0.0)',  # Changed to transparent
            'padding': '15px',
            'borderRadius': '15px',
            'boxShadow': '0 8px 30px rgba(0, 0, 0, 0.5)',  # Unchanged
            'color': '#FFFFFF',
            'flex': '1',
            'border': '1px solid rgba(255, 255, 255, 0.5)'  # Changed to light grey
        }

    def data_box_style_blue(self):
        """Style for data boxes with a teal tinge.""" 
        return {
            'backgroundColor': 'rgba(0, 128, 128, 0.1)',  # Light teal tinge
            'padding': '15px',
            'borderRadius': '15px',
            'boxShadow': '0 8px 30px rgba(0, 0, 0, 0.5)',  # Unchanged
            'color': '#FFFFFF',
            'flex': '1',
            'border': '1px solid rgba(255, 255, 255, 0.5)'  # Light grey border
        }

    def callbacks(self):
        """Define the callbacks for dynamic updates."""

        @self.app.callback(
            [Output("sonarr-activities", "children"),
             Output("radarr-activities", "children"),
             Output("qbittorrent-activities", "children"),
             Output("speed-graph", "figure")],
            [Input("update-interval", "n_intervals")]
        )
        def update_dashboard(n):
            # Fetch data
            sonarr_data = self.fetch_sonarr_activities()
            radarr_data = self.fetch_radarr_activities()
            torrents, transfer_info = self.fetch_qbittorrent_stats()

            # Update speed tracking
            self.download_speeds.append(transfer_info.get("dl_info_speed", 0) / 1024 / 1024)  # Convert to MB/s
            self.upload_speeds.append(transfer_info.get("up_info_speed", 0) / 1024 / 1024)  # Convert to MB/s

            # Get the current time
            from datetime import datetime
            current_time = datetime.now()

            # Process Sonarr Data
            sonarr_content = [
                html.Div(
                    html.Div(
                        f"Season {item.get('seasonNumber', 'N/A')}x{item.get('episodeNumber', 'N/A')} - {item.get('title', 'Unknown Title')} - {self.time_until_release(item['airDateUtc'], current_time)}", 
                        style=self.data_box_style()
                    ), 
                    style={'marginBottom': '10px'}  # Add margin between data divs
                )
                for item in sonarr_data
            ] or [html.Div("No upcoming episodes", style={'color': '#AAAAAA'})]

            # Process Radarr Data
            radarr_content = [
                html.Div(
                    html.Div(f"{item['title']} - {self.time_until_release(item['releaseDate'], current_time)}", style=self.data_box_style()), 
                    style={'marginBottom': '10px'}  # Add margin between data divs
                )
                for item in radarr_data
            ] or [html.Div("No upcoming movies", style={'color': '#AAAAAA'})]

            # Process qBittorrent Data, filtering out any activities with <td> tags
            qbittorrent_content = [
                html.Div(
                    html.Div(
                        f"{torrent['name']} - {torrent['progress']*100:.2f}% complete", 
                        style=self.data_box_style_green() if torrent['progress'] == 1 else self.data_box_style_blue() if torrent['progress'] > 0 else self.data_box_style()  # Use blue style if in progress
                    ), 
                    style={'marginBottom': '10px'}  # Add margin between data divs
                )
                for torrent in torrents if not any('td' in str(value) for value in [torrent['name'], torrent.get('status', ''), torrent.get('size', '')])  # Check relevant fields for <td> tags
            ] or [html.Div("No active torrents", style={'color': '#AAAAAA'})]

            # Create Speed Graph
            figure = go.Figure()
            figure.add_trace(go.Scatter(
                y=list(self.download_speeds)[-108:],  # Show last 2160 results
                mode='lines',
                name='Download Speed (MB/s)',
                line=dict(color='orange', width=2)
            ))
            figure.add_trace(go.Scatter(
                y=list(self.upload_speeds)[-2160:],  # Show last 2160 results
                mode='lines',
                name='Upload Speed (MB/s)',
                line=dict(color='teal', width=2)
            ))
            figure.update_layout(
                title="Download & Upload Speeds",
                xaxis_title="Time (Intervals)",
                yaxis_title="Speed (MB/s)",
                paper_bgcolor="rgba(0, 0, 0, 0)",
                plot_bgcolor="rgba(0, 0, 0, 0)",
                font=dict(color="#FFFFFF"),
                legend=dict(
                    bgcolor="rgba(0, 0, 0, 0)", 
                    bordercolor="rgba(0, 0, 0, 0)",
                    orientation='h',  # Set legend orientation to horizontal
                    yanchor='top',    # Anchor the legend to the top
                    y=-0.2,           # Position the legend below the graph
                    xanchor='center', # Center the legend
                    x=0.5             # Center the legend horizontally
                ),
                xaxis=dict(showline=False, showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showline=False, showgrid=False, zeroline=False),
                hovermode='x unified'
            )

            return sonarr_content, radarr_content, qbittorrent_content, figure

    def fetch_sonarr_activities(self):
        """Fetch Sonarr calendar data for the upcoming week."""
        try:
            from datetime import datetime, timedelta
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)  # One week from now
            url = f"{self.SONARR_API}/calendar"
            params = {
                "apikey": self.SONARR_KEY,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
            response = requests.get(url, params=params)
            print(response.text)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Sonarr API error: {e}")
            return []

    def fetch_radarr_activities(self):
        """Fetch Radarr calendar data for the upcoming week."""
        try:
            from datetime import datetime, timedelta
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)  # One week from now
            url = f"{self.RADARR_API}/calendar"
            params = {
                "apikey": self.RADARR_KEY,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Radarr API error: {e}")
            return []

    def fetch_qbittorrent_stats(self):
        """Fetch qBittorrent data."""
        try:
            session = requests.Session()
            session.post(f"{self.QBITTORRENT_API}/auth/login", data={
                "username": self.QBITTORRENT_USERNAME,
                "password": self.QBITTORRENT_PASSWORD
            })

            torrents = session.get(f"{self.QBITTORRENT_API}/torrents/info").json()
            transfer_info = session.get(f"{self.QBITTORRENT_API}/transfer/info").json()
            return torrents, transfer_info
        except Exception as e:
            print(f"qBittorrent API error: {e}")
            return [], {}

    def time_until_release(self, release_time_str, current_time):
        """Calculate the time until release."""
        from datetime import datetime
        release_time = datetime.fromisoformat(release_time_str[:-1])  # Convert to datetime object
        time_diff = release_time - current_time

        if time_diff.total_seconds() < 0:
            return "Released"
        
        days, seconds = time_diff.days, time_diff.seconds
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        return f"{days}d {hours}h {minutes}m"

    def run(self):
        """Run the Dash app."""
        self.app.run_server(host='0.0.0.0', port=8051, debug=False)


# Run the dashboard
if __name__ == "__main__":
    dashboard = MediaDashboard()
    dashboard.run()