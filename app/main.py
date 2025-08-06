import uvicorn
from app.settings import Settings


def main():

    port = Settings.PORT
    host = Settings.HOST
    
    uvicorn.run(
        app="app.core.config:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()
