#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
freqtrade-discord
An unofficial discord bot to view and control freqtrade bots, much like
the telegram implementation.

NB: This discord bot requires the 'message_content' intent to be set
in the Discord Developer portal for this app.

Licence: MIT [https://github.com/froggleston/freqtrade-frogtrade9000/blob/main/LICENSE]

Donations:
    BTC: bc1qxdfju58lgrxscrcfgntfufx5j7xqxpdufwm9pv
    ETH: 0x581365Cff1285164E6803C4De37C37BbEaF9E5Bb

Conception Date: 2023-03-17

"""

import aiohttp
import argparse
import discord
import traceback

from tabulate import tabulate

token = None
auth = None
servers = {}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    cmd_string = message.content.split(" ")
    cmd = cmd_string[0]

    if cmd.startswith('$servers'):
        resp = []
        headers = ["NAME","IP","PORT"]
        resp.append(headers)

        for k,v in servers.items():
            resp.append([k,v['ip'],v['port']])
        table = tabulate(resp,headers='firstrow',tablefmt='grid')
        await message.channel.send(f"```{table}```")
    else:
        if len(cmd_string) > 1:
            server = cmd_string[1]
        else:
            return "ERROR: No server specified. Run `$servers` to list them."

        ip = servers[server]['ip']
        port = servers[server]['port']
        auth = servers[server]['auth']

        if cmd.startswith('$ping'):
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{ip}:{port}/api/v1/ping') as r:
                    if r.status == 200:
                        js = await r.json()
                        embeds = [
                            {"title":"PING",
                             "fields":[{"name":"Response","value":js['status']}]
                            }
                        ]
                        embed = discord.Embed.from_dict(embeds[0])
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send(f"Error: Status {r.status} received.")

        if cmd.startswith('$status'):
            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.get(f'http://{ip}:{port}/api/v1/status') as r:
                    if r.status == 200:
                        js = await r.json()
                        resp = []
                        headers = ["ID","PAIR","PROFIT %","PROFIT"]
                        resp.append(headers)
                        for trade in js:
                            resp.append(
                                [trade['trade_id'],
                                 trade['pair'],
                                 trade['current_profit_pct'],
                                 f"{trade['current_profit_abs']} {trade['quote_currency']}"
                                ]
                            )
                        table = tabulate(resp,headers='firstrow',tablefmt='grid')
                        await message.channel.send(f"```{table}```")
                    else:
                        await message.channel.send(f"Error: Status {r.status} received.")


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--yaml", nargs='?', help="Supply a YAML file.")
    args = parser.parse_args()

    if args.yaml is not None:
        import yaml
        with open(args.yaml, 'r') as yamlfile:
            args = dotdict(yaml.safe_load(yamlfile))
            args.yaml = True

    if args.yaml:
        token = args.token
        for s in args.servers:
            server = {}
            server['ip'] = s['ip']
            server['port'] = s['port']
            server['auth'] = aiohttp.BasicAuth(login=s['username'],
                                               password=s['password'],
                                               encoding='utf-8')
            servers[s['name']] = server

        client.run(token)
    else:
        raise Exception("No YAML file supplied.")

if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        traceback.print_exc()
        print("You got frogged: ", e)
