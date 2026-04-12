from data.database import init_db
from ui.app import App

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()