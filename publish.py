"""Assemble chunk videos + soundtrack, then upload to YouTube as private with a scheduled publishAt.
Usage: python publish.py <chunks_dir> <publish_at ISO8601 UTC>
       python publish.py --upload-only <mp4> <publish_at> [thumb]"""
import csv, datetime, glob, json, os, subprocess, sys
import theme as T
import meta as Meta

HERE = os.path.dirname(os.path.abspath(__file__))


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def assemble(chunks_dir):
    parts = sorted(glob.glob(os.path.join(chunks_dir, "**", "chunk_*.mp4"), recursive=True))
    if not parts:
        sys.exit("no chunks found")
    lst = os.path.join(HERE, "parts.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{os.path.abspath(p)}'\n")
    wav = os.path.join(HERE, f"audio_{T.TAG}.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "post.py"), "--audio", wav], check=True)
    out = os.path.join(HERE, f"final_{T.TAG}.mp4")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    return out, len(parts)


def yt():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
                        client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def add_to_playlist(client, playlist_id, video_id):
    have = client.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50).execute().get("items", [])
    if any(i["contentDetails"]["videoId"] == video_id for i in have):
        return
    client.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()


def add_to_playlists(client, vid):
    path = os.path.join(HERE, "playlists.json")
    if not os.path.exists(path):
        return
    ids = json.load(open(path))
    key = "countries" if T.THEME == "countries" else "colors"
    for k in (key, "all"):
        if k in ids:
            try:
                add_to_playlist(client, ids[k], vid)
            except Exception as e:
                print("playlist skipped:", e)


def upload(mp4, publish_at, thumb=None):
    from googleapiclient.http import MediaFileUpload
    title, desc, tags = Meta.meta()
    now = datetime.datetime.now(datetime.timezone.utc)
    when = datetime.datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    status = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": False, "embeddable": True}
    if when > now + datetime.timedelta(minutes=20):
        status.update(privacyStatus="private", publishAt=when.strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        status.update(privacyStatus="public")  # slot already passed: publish right away
    body = {"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "24",
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": status}
    client = yt()
    want = os.environ.get("YT_CHANNEL_ID")
    if want:
        mine = client.channels().list(part="id", mine=True).execute()["items"][0]["id"]
        if mine != want:
            sys.exit(f"token belongs to {mine}, expected {want}")
    import time
    for attempt in range(4):  # Google arada geçici 401 veriyor (özellikle yeni tokenlarda): yeni bağlantıyla tekrar
        try:
            req = client.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(
                mp4, mimetype="video/mp4", resumable=True, chunksize=-1))
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
            break
        except Exception as e:  # noqa: BLE001
            if "401" not in str(e) or attempt == 3:
                raise
            print("transient 401, retrying", attempt + 1, flush=True)
            time.sleep(20 * (attempt + 1))
            client = yt()
    vid = resp["id"]
    add_to_playlists(client, vid)
    if thumb and os.path.exists(thumb):
        try:
            client.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb, mimetype="image/jpeg")).execute()
        except Exception as e:  # custom thumbnails need a verified channel
            print("thumbnail skipped:", e)
    return vid, title, status.get("publishAt", "now")


def log(vid, title, when):
    d = os.path.join(HERE, "records", "published")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, T.TAG + ".csv"), "w", newline="") as fh:
        csv.writer(fh).writerow([T.CFG, vid, when, title])


if __name__ == "__main__":
    if sys.argv[1] == "--upload-only":
        mp4, publish_at = sys.argv[2], sys.argv[3]
        thumb = sys.argv[4] if len(sys.argv) > 4 else None
        vid, title, when = upload(mp4, publish_at, thumb)
        log(vid, title, when)
        print("uploaded", vid, title, when)
        sys.exit()
    chunks, publish_at = sys.argv[1], sys.argv[2]
    mp4, n = assemble(chunks)
    print("assembled", mp4, n, "chunks")
    if not all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")):
        print("YouTube secrets missing: queued in records/pending, video kept as artifact")
        os.makedirs(os.path.join(HERE, "records", "pending"), exist_ok=True)
        with open(os.path.join(HERE, "records", "pending", T.TAG + ".csv"), "w", newline="") as fh:
            csv.writer(fh).writerow([T.CFG, publish_at, os.environ.get("GITHUB_RUN_ID", ""), T.TAG])
        sys.exit(0)
    vid, title, when = upload(mp4, publish_at)
    log(vid, title, when)
    print("uploaded", vid, title, when)
