This script will track the amount of spawned/killed special tameable pets and it's rarity version. On UOAlive some tameable pets have exotic, eqxuisite, rare and legadary versions. 

[Changelog](CHANGELOG.md)

Currently supported:
Ki-Rin
Nightmare
Undead Ossein Ram
Shadow Wyrm
Phoenix
Cu Sidhe
Polar Bears
Tsuki Wolf

Statistics are saved every 10 seconds. The tracker creates a timestamped
backup on startup and every hour in `pet_hunt_tracker_backups`, retaining the
newest 30 backups. Change `BACKUP_INTERVAL_SECONDS` and `BACKUP_RETENTION` near
the top of the script to adjust this behavior.
