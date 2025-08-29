# 🎮 Esports World Cup API

A comprehensive Flask-based REST API for esports data, providing real-time information about tournaments, teams, players, matches, and news for the Esports World Cup and other major esports events.

## 🌟 Features

- **📰 News Management** - CRUD operations for esports news with image upload support
- **🏆 Tournament Information** - Detailed data about EWC and other tournaments
- **👥 Teams & Players** - Comprehensive player transfers, team rosters, and profiles
- **⚔️ Matches & Schedules** - Live and upcoming match data across multiple games
- **🏅 Prize Distribution** - Prize pool information and distribution details
- **🔍 Advanced Search** - Full-text and fuzzy search across all data types
- **📊 Rankings** - EWC club championship standings with weekly tracking
- **🔄 Live Data Fetching** - Real-time data scraping from Liquipedia
- **📱 Pagination & Filtering** - Efficient data retrieval with extensive filtering options

## 🛠️ Technology Stack

- **Backend Framework**: Flask (Python)
- **Database**: SQLite with FTS5 for full-text search
- **API Documentation**: Flasgger/Swagger
- **CORS Support**: Flask-CORS
- **Data Scraping**: BeautifulSoup, Requests
- **Search**: FuzzyWuzzy for fuzzy search, SQLite FTS5 for full-text
- **Authentication**: (To be implemented based on requirements)

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/mahmoodhamdi/esports-flask.git
cd esports-flask
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Initialize the database**
```bash
python -c "from app import create_app; app = create_app()"
```

5. **Run the application**
```bash
python run.py
```

The API will be available at `http://localhost:5000`

## 📚 API Documentation

Once the application is running, access the interactive Swagger documentation at:
`http://localhost:5000/apidocs`

## 🗂️ Project Structure

```
esports-flask/
├── app/
│   ├── __init__.py          # Application factory and setup
│   ├── db.py               # Database connection and initialization
│   ├── enhanced_search.py  # Advanced search functionality
│   ├── ewc_info.py         # EWC tournament information
│   ├── ewc_rank.py         # Club championship rankings
│   ├── ewc_teams_players.py # Teams and players data
│   ├── game_matches.py     # Match data handling
│   ├── fuzzy_search.py     # Fuzzy search implementation
│   └── fts_search.py       # Full-text search implementation
├── routes/                 # API route handlers
├── static/                 # Static files and uploads
└── Esports.postman_collection.json  # Postman collection for testing
```

## 🚀 Key API Endpoints

### News
- `GET /api/news` - Retrieve news articles
- `POST /api/news` - Create a new news article
- `PUT /api/news/{id}` - Update a news article
- `DELETE /api/news/{id}` - Delete a news article

### Tournaments & Matches
- `GET /api/ewc_info` - EWC tournament information
- `GET /api/ewc_matches` - EWC matches data
- `GET /api/game_matches` - Matches for specific games
- `GET /api/global-matches` - Global matches across all games

### Teams & Players
- `GET /api/ewc_teams` - EWC participating teams
- `GET /api/ewc_teams_players` - Team rosters and player information
- `GET /api/player-transfers` - Player transfer information
- `GET /api/team_information` - Detailed team information
- `GET /api/player_information` - Detailed player information

### Rankings & Prizes
- `GET /api/ewc_rank` - Club championship standings
- `GET /api/ewc_prize_distribution` - Prize distribution information

### Search
- `GET /api/search` - Global search across all data
- `GET /api/extended/search` - Advanced search with filters

## 🔧 Configuration

The application can be configured through environment variables:

- `FLASK_ENV` - Environment (development/production)
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Allowed origins for CORS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Developer

**Mahmood Hamdi**  
- Email: [hmdy7486@gmail.com](mailto:hmdy7486@gmail.com)  
- WhatsApp: [+201019793768](https://wa.me/201019793768)  
- GitHub: [https://github.com/mahmoodhamdi/](https://github.com/mahmoodhamdi/)

## 🙏 Acknowledgments

- Liquipedia for providing comprehensive esports data
- Flask community for excellent documentation and resources
- All contributors who have helped improve this project
