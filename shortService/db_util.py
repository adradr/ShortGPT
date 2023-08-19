# Assuming video_output_path is the path to the video file you want to copy to the database
import os
import sqlite3


def store_content_in_db(
    content_type: str,
    content_name: str,
    content_url: str,
    content_description: str,
    db_path: str = "/app/db/content.db",
):
    """Stores a video in a SQLite database

    Args:
        video_output_path (str): path to the video file
    """

    # Connect to the SQLite database and create a table if it doesn't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS content (id INTEGER PRIMARY KEY, type TEXT, name TEXT, url TEXT, rendered BOOLEAN, uploaded BOOLEAN, description TEXT)"
    )

    # Insert the video file's name and data into the videos table
    cursor.execute(
        "INSERT INTO content (type, name, url, rendered, uploaded, description) VALUES (?, ?, ?, ?, ?, ?)",
        (content_type, content_name, content_url, False, False, content_description),
    )
    conn.commit()
    conn.close()


def read_content_from_db(content_name, db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "SELECT type, name, url, rendered, uploaded, description FROM content WHERE name=?",
        (content_name,),
    )
    (
        content_type,
        content_name,
        content_url,
        content_rendered,
        content_uploaded,
        content_description,
    ) = cursor.fetchone()
    conn.close()

    return (
        content_type,
        content_name,
        content_url,
        content_rendered,
        content_uploaded,
        content_description,
    )


def set_content_rendered(content_name, db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "UPDATE content SET rendered=? WHERE name=?",
        (
            True,
            content_name,
        ),
    )
    conn.commit()
    conn.close()


def read_contents_to_render(db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "SELECT name FROM content WHERE rendered=?",
        (False,),
    )
    contents = cursor.fetchall()
    conn.close()

    return contents


def read_contents_to_upload(db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "SELECT name FROM content WHERE uploaded=?",
        (False,),
    )
    contents = cursor.fetchall()
    conn.close()

    return contents


def set_content_uploaded(content_name, db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "UPDATE content SET uploaded=? WHERE name=?",
        (
            True,
            content_name,
        ),
    )
    conn.commit()
    conn.close()


def store_video_in_db(
    video_output_path: str,
    video_title: str,
    video_description: str,
    db_path: str = "/app/db/content.db",
):
    """Stores a video in a SQLite database

    Args:
        video_output_path (str): path to the video file
    """

    # Connect to the SQLite database and create a table if it doesn't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY, name TEXT, data BLOB, ext TEXT, description TEXT)"
    )

    # Read the video file as binary data
    with open(video_output_path, "rb") as f:
        video_data = f.read()
    # Insert the video file's name and data into the videos table
    video_ext = video_output_path.split(".")[-1]
    cursor.execute(
        "INSERT INTO videos (name, data, ext, description) VALUES (?, ?, ?, ?)",
        (video_title, video_data, video_ext, video_description),
    )
    conn.commit()
    conn.close()


def read_video_from_db(video_name, db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute(
        "SELECT id, name, description, data, ext FROM videos WHERE name=?",
        (video_name,),
    )
    id, video_name, video_description, video_data, video_ext = cursor.fetchone()
    if not video_name:
        return None, None
    # Write the video file to a temporary file
    video_path = f"{id}.{video_ext}"
    video_save_path = os.path.join("/app/tmp", video_path)
    os.makedirs(os.path.dirname(video_save_path), exist_ok=True)
    with open(video_save_path, "wb") as f:
        f.write(video_data)
        print("Video saved to: ", video_save_path)
    conn.close()

    return video_save_path, video_description


def remove_video_from_db(video_name, db_path="/app/db/content.db"):
    """Reads a video from a SQLite database

    Args:
        video_id (int): id of the video to read
    """

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Select the video file from the database
    cursor.execute("DELETE FROM videos WHERE name=?", (video_name,))
    conn.commit()
    conn.close()
