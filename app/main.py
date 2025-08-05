from core import app, logger_init

def main():
    import uvicorn
    port = logger_init()
    uvicorn.run(app, host="0.0.0.0", port=port)
    
if __name__ == "__main__":
    main()
