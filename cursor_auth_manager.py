import sqlite3
import os
import sys

class CursorAuthManager:
    """Cursor authentication information manager"""

    def __init__(self):
        # Determine the operating system
        if sys.platform == "win32":  # Windows
            appdata = os.getenv("APPDATA")
            if appdata is None:
                raise EnvironmentError("APPDATA environment variable is not set")
            self.db_path = os.path.join(
                appdata, "Cursor", "User", "globalStorage", "state.vscdb"
            )
        elif sys.platform == "darwin": # macOS
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
            ))
        elif sys.platform == "linux" : # Linux and other Unix-like systems
            self.db_path = os.path.abspath(os.path.expanduser(
                "~/.config/Cursor/User/globalStorage/state.vscdb"
            ))
        else:
            raise NotImplementedError(f"Unsupported operating system: {sys.platform}")

    def update_auth(self, email=None, access_token=None, refresh_token=None):
        updates = []
        updates.append(("cursorAuth/cachedSignUpType", "Auth_0"))

        if email is not None:
            updates.append(("cursorAuth/cachedEmail", email))
        if access_token is not None:
            updates.append(("cursorAuth/accessToken", access_token))
        if refresh_token is not None:
            updates.append(("cursorAuth/refreshToken", refresh_token))

        if not updates:
            print("No values provided to update")
            return False

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in updates:
                # If no rows are updated, it means the key does not exist, so perform an insert
                # Check if accessToken exists
                check_query = f"SELECT COUNT(*) FROM itemTable WHERE key = ?"
                cursor.execute(check_query, (key,))
                if cursor.fetchone()[0] == 0:
                    insert_query = "INSERT INTO itemTable (key, value) VALUES (?, ?)"
                    cursor.execute(insert_query, (key, value))
                else:
                    update_query = "UPDATE itemTable SET value = ? WHERE key = ?"
                    cursor.execute(update_query, (value, key))

                if cursor.rowcount > 0:
                    print(f"Successfully updated {key.split('/')[-1]}")
                else:
                    print(f"Could not find {key.split('/')[-1]} or value has not changed")

            conn.commit()
            return True

        except sqlite3.Error as e:
            print("Database error:", str(e))
            return False
        except Exception as e:
            print("An error occurred:", str(e))
            return False
        finally:
            if conn:
                conn.close()
