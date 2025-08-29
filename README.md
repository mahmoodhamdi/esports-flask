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
- **📊 Matches Dashboard** - Comprehensive match viewing interface
- **🗓️ Weekly Tracking** - Week-by-week EWC progress and statistics

## 🛠️ Technology Stack

- **Backend Framework**: Flask (Python)
- **Database**: SQLite with FTS5 for full-text search
- **API Documentation**: Flasgger/Swagger
- **CORS Support**: Flask-CORS
- **Data Scraping**: BeautifulSoup, Requests
- **Search**: FuzzyWuzzy for fuzzy search, SQLite FTS5 for full-text
- **Data Processing**: Pandas for data manipulation
- **Authentication**: (To be implemented based on requirements)

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtualenv (recommended)

### Installation Steps

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

### Docker Installation (Alternative)
```bash
docker build -t esports-api .
docker run -p 5000:5000 esports-api
```

## 📚 API Documentation

Once the application is running, access the interactive Swagger documentation at:
`http://localhost:5000/apidocs`

## 🗂️ Project Structure

```
esports-flask/
├── app/
│   ├── __init__.py              # Application factory and setup
│   ├── db.py                    # Database connection and initialization
│   ├── enhanced_search.py       # Advanced search functionality
│   ├── ewc_info.py              # EWC tournament information
│   ├── ewc_rank.py              # Club championship rankings
│   ├── ewc_teams_players.py     # Teams and players data
│   ├── game_matches.py          # Match data handling
│   ├── fuzzy_search.py          # Fuzzy search implementation
│   ├── fts_search.py            # Full-text search implementation
│   ├── matches_mohamed.py       # Match scraping functionality
│   ├── news.py                  # News management
│   ├── new_teams.py             # Teams data handling
│   ├── game_teams.py            # Game teams management
│   └── game_teams_init_db.py    # Database initialization for game teams
├── routes/                      # API route handlers
│   ├── news.py
│   ├── games.py
│   ├── prizes.py
│   ├── info.py
│   ├── player_transfers.py
│   ├── ewc_rank_route.py
│   ├── ewc_teams_players.py
│   ├── team_information.py
│   ├── player_information.py
│   ├── search.py
│   ├── search_extended.py
│   ├── game_matches.py
│   ├── game_teams.py
│   └── ewc_weeks.py
├── matches_dashborad/           # Matches dashboard functionality
│   └── reoute_matches_dashbord_test.py
├── static/                      # Static files and uploads
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## 🚀 Complete API Endpoints

### News Management
- `GET /api/news` - Retrieve paginated news articles with filtering
- `POST /api/news` - Create a new news article
- `GET /api/news/{id}` - Get a specific news article
- `PUT /api/news/{id}` - Update a news article
- `DELETE /api/news/{id}` - Delete a news article
- `DELETE /api/news` - Delete all news articles

### Games Information
- `GET /api/games` - Get information about supported games

### Prize Distribution
- `GET /api/prizes` - Get prize pool information and distribution

### General Information
- `GET /api/info` - Get general EWC tournament information

### Player Transfers
- `GET /api/player-transfers` - Get player transfer information

### EWC Rankings
- `GET /api/ewc_rank` - Get club championship standings

### EWC Teams & Players
- `GET /api/ewc_teams_players` - Get team rosters and player data

### Team Information
- `GET /api/team_information` - Get detailed team profiles

### Player Information
- `GET /api/player_information` - Get detailed player profiles

### Search Functionality
- `GET /api/search` - Basic search across all data types
- `GET /api/extended/search` - Advanced search with filters

### Game Matches
- `GET /api/game_matches` - Get match data for specific games
- `GET /api/game_matches/{game}` - Get matches for a specific game

### Teams Data
- `GET /api/new_teams` - Get team information from JSON data
- `POST /api/new_teams` - Add new team data
- `GET /api/game_teams` - Get teams for specific games

### Matches Dashboard
- `GET /api/matches` - Get matches dashboard data with filtering
- `GET /api/matches/{game}` - Get matches for a specific game

### EWC Weeks
- `GET /api/weeks` - Get weekly EWC information and progress

### File Uploads
- `GET /uploads/{filename}` - Serve uploaded files

## 🔧 Configuration

The application can be configured through environment variables:

- `FLASK_ENV` - Environment (development/production)
- `FLASK_DEBUG` - Debug mode (0/1)
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Allowed origins for CORS
- `HOST` - Host address to bind to (default: 0.0.0.0)
- `PORT` - Port to run on (default: 5000)

Example environment file (.env):
```env
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=sqlite:///app.db
CORS_ORIGINS=*
HOST=0.0.0.0
PORT=5000
```

## 🗄️ Database Schema

The application uses SQLite with the following main tables:
- `news` - News articles with metadata
- `matches` - Match information across games
- `game_teams` - Team information for specific games
- `game_teams_fts` - Full-text search virtual table

## 🔍 Search Features

### Full-Text Search
- Supports searching across team names, game names, and logo modes
- Uses SQLite FTS5 for efficient text searching
- Automatic synchronization with triggers

### Fuzzy Search
- Implemented using FuzzyWuzzy
- Handles typos and approximate matching
- Configurable similarity thresholds

### Extended Search
- Advanced filtering options
- Field-specific search capabilities
- Combined text and filter queries

## 📊 Data Sources

The API integrates with multiple data sources:
- **Liquipedia** - For live match data and tournament information
- **Local JSON files** - For team and game data
- **Manual input** - For news and custom content

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide for Python code
- Write tests for new functionality
- Update documentation for new features
- Use descriptive commit messages

## 🧪 Testing

Run the test suite with:
```bash
python -m pytest tests/ -v
```

Or run specific test files:
```bash
python -m pytest tests/test_news.py -v
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Database errors**: Try deleting the database file and reinitializing
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **CORS issues**: Check the CORS_ORIGINS environment variable
4. **File upload issues**: Ensure the uploads directory exists and has proper permissions

### Getting Help

If you encounter issues not covered here, please:
1. Check the existing issues on GitHub
2. Create a new issue with detailed information
3. Include error logs and steps to reproduce

## 👨‍💻 Developer

**Mahmood Hamdi**  
- Email: [hmdy7486@gmail.com](mailto:hmdy7486@gmail.com)  
- WhatsApp: [+201019793768](https://wa.me/201019793768)  
- GitHub: [https://github.com/mahmoodhamdi/](https://github.com/mahmoodhamdi/)

## 🙏 Acknowledgments

- Liquipedia for providing comprehensive esports data
- Flask community for excellent documentation and resources
- All contributors who have helped improve this project
- The esports community for feedback and feature suggestions

---

**Note**: This API is actively maintained and updated regularly with new features and improvements. Check the GitHub repository for the latest updates and release notes.