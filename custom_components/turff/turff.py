import asyncio
import json
import socket
import datetime

import aiohttp
import async_timeout
from yarl import URL

from .const import API_HOST
from .exceptions import TurffConnectionError, TurffCredentialsError, TurffError

REQUEST_LIMIT = 2

class Turff:
    def __init__(
        self,
        username: str,
        password: str,
        loop=None,
        request_timeout: int = 10,
        session=None,
    ):
        self._loop = loop
        self._session = session
        self._close_session = False

        self.username = username
        self.password = password
        self.cookie = None
        self.house_id = None

        self.request_timeout = request_timeout

        if self._loop is None:
            self._loop = asyncio.get_event_loop()

        if self._session is None:
            self._session = aiohttp.ClientSession(loop=self._loop)
            self._close_session = True

    async def _request(
        self, uri: str, method: str = "POST", data=None, full_response=False
    ):
        """Handle a request to Turff API"""
        url = URL.build(scheme="https", host=API_HOST, port=443).join(URL(uri))

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Cookie": self.cookie or "",
        }

        try:
            with async_timeout.timeout(self.request_timeout):
                response = await self._session.request(
                    method, url, json=data, headers=headers, ssl=True
                )
        except asyncio.TimeoutError as exception:
            raise TurffConnectionError(
                "Timeout occurred while connecting to Turff API."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise TurffConnectionError(
                "Error occurred while communicating with Turff."
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if (response.status // 100) in [4, 5]:
            contents = await response.read()
            response.close()

            if content_type == "application/json":
                raise TurffError(response.status, json.loads(contents.decode("utf8")))
            raise TurffError(response.status, {"message": contents.decode("utf8")})

        if full_response:
            return response

        if "application/json" in response.headers["Content-Type"]:
            return await response.json()
        return await response.text()

    @property
    def connected(self):
        return self.cookie and self.house_id

    async def validate_credentials(self):
        """ Check if the credentials are valid by trying to login """
        try:
            await self._connect()
            return True
        except TurffCredentialsError:
            pass

        return False

    async def get_house_name(self):
        house = await self._get_house()

        return house["info"]["name"]

    async def get_products(self):
        house = await self._get_house()

        return house["tablet"]["items"]

    async def get_product_balance(self, product_id):
        if not self.connected:
            await self._connect()

        response = await self._request(
            f"api/tablet/{self.house_id}/getStands", data={"itemUID": product_id}
        )
        balance_by_user = {u["alias"]: u["stand"] for u in response}

        return balance_by_user

    async def get_consumption_history(self, product_id, days=31):
        if not self.connected:
            await self._connect()

        consumption_by_user = await self._parse_consumption_list(product_id, days)
        consumption_by_user = list(consumption_by_user.values())

        # Add week and month values
        if days >= 7:
            for u in consumption_by_user:
                u['week'] = (sum(u[i] for i in range(7)))

                if days >= 31:
                    u['month'] = (sum(u[i] for i in range(31)))

        return consumption_by_user

    async def _get_house(self):
        if not self.connected:
            await self._connect()

        return await self._request(f"api/house/{self.house_id}", method="GET")

    async def _connect(self):
        """
        Connect to the API.
        First login using username and password.
        After that obtain the house id (which is needed for all API calls)
        """
        if not self.cookie:
            await self._login()
        if not self.house_id:
            await self._set_house_id()

    async def _login(self):
        """ Login to the API and extract the authentication Cookie """
        response = await self._request(
            "auth/auth/login",
            data={"type": "local", "email": self.username, "password": self.password},
            full_response=True,
        )

        if (await response.text()) == "Inlog gegevens kloppen niet":
            raise TurffCredentialsError("Turff Credentials Invalid")

        self.cookie = response.cookies

    async def _set_house_id(self):
        response = await self._request("api/house", method="GET")

        self.house_id = response["houses"][0]["UID"]

    async def _parse_consumption_list(self, product_id, days):
        today = datetime.date.today()
        consumption_by_user = {}
        offset = 0

        while True:
            response = await self._consumption_request(product_id, offset)
            for u in response:
                if u['artificial']: # if this was done via the website, so when new beer is bought
                    continue

                name = u['alias'] or u['groupName']
                if name not in consumption_by_user:
                    consumption_by_user[name] = {i: 0 for i in range(days)}
                    consumption_by_user[name]['name'] = name

                u_date = datetime.datetime.strptime(u['time_stamp'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
                diff = (today - u_date).days

                # If we reached the limit
                if diff >= days:
                    return consumption_by_user

                consumption_by_user[name][diff] += u['amount']

            offset += REQUEST_LIMIT



    async def _consumption_request(self, product_id, offset=0):
        return await self._request(
            f"api/tablet/{self.house_id}/log", data={"itemUID": product_id, "limit": REQUEST_LIMIT, "offset": offset}
        )
