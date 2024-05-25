from instagrapi import Client


def main():

    emails = []
    # list with ids, if you want to search by username use user_id_from_username(username: str)
    list_ids_users = "list_ids.txt"

    with open("credentials.txt", "r") as f:
        username, password = f.read().splitlines()

    client = Client()
    client.login(username, password, verification_code="6719 4253")

    with open(list_ids_users, "r") as list_usernames:
        list_ids = list_usernames.read()

        for curr_id in list_ids:
            # client.user_info_by_username(curr_id).dict()
            print(client.user_info_by_username(curr_id).dict())


if __name__ == "__main__":
    main()
