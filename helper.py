from discord.ext import commands
from colorama import Fore, init
from embeds import HelperEmbed, now
from datetime import datetime
import requests
import discord
import helheim
import cloudscraper
import discord.ext
import pysftp
import io


init()

helheim.auth('')

RED = discord.Colour.red()
BLUE = discord.Colour.blue()
GREEN = discord.Colour.green()

client = commands.Bot(command_prefix="!")

def injection(session, response):
    if helheim.isChallenge(session, response):
        return helheim.solve(session, response)
    return response

global scraper
scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome', # we want a chrome user-agent
                'mobile': False, # pretend to be a desktop by disabling mobile user-agents
                'platform': 'windows' # pretend to be 'windows' or 'darwin' by only giving this type of OS for user-agents
            },
            requestPostHook=injection,
            captcha={"provider": "vanaheim"}
        )
helheim.wokou(scraper)

def upload_pids_ftp(pids: list):
    HOST = ""
    USER = ""
    PASS = ""
    CNOPTS = pysftp.CnOpts()
    CNOPTS.hostkeys = None

    buffer = io.BytesIO("\n".join(pids).encode("utf-8"))
    with pysftp.Connection(HOST, USER, password=PASS, cnopts=CNOPTS) as sftp:
        print(f"[{now()}] Connection established {HOST}: ATTEMPTING TO UPDATE pids.txt")
        sftp.chdir("jheels/")
        sftp.putfo(buffer, "pids.txt")

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command doesn't exist")
        return
    elif isinstance(error, commands.errors.PrivateMessageOnly):
        await ctx.send("DM only command")
        return
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("You do not have permission!")
        return
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("Missing a required argument!")
        return
    raise error

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(name="!info"))
    print("Bot is ready...")

@commands.dm_only()
@client.command()
async def info(ctx):
    embed = HelperEmbed(ctx, "https://www.currys.co.uk/").base_embed(BLUE, "List of Commands")
    embed.add_field(name="!info", value="Retrieve this embed", inline=False)
    embed.add_field(name="!add <pid>", value="Add PID to the monitor", inline=False)
    embed.add_field(name="!remove <pid(s)>", value="Remove PID(s) from monitor; delimit by space", inline=False)
    embed.add_field(name="!clear", value="Clears all PIDS from monitor", inline=False)
    await ctx.send(embed=embed)

@commands.dm_only()
@client.command()
async def add(ctx,*, pid: str):
    url = f"https://www.currys.co.uk/GBUK/product-{pid}-pdt.html"
    helper_embed = HelperEmbed(ctx, url)
    print(Fore.CYAN + f"[{now()}] [HELPER] {ctx.author.display_name} ATTEMPTING ADD: {pid}")
    
    if len(pid) != 8 or not pid.isdigit():
        embed = helper_embed.invalid_embed(pid, "Invalid PID Format")
        print(f"{Fore.RED}[{now()}] [HELPER] {ctx.author.display_name} FAILED TO ADD: {pid}")
        await ctx.send(embed=embed)
        return

    await ctx.send("Request received")
    with scraper as session:
        try:
            pids = requests.get("pids.txt", timeout=20).text.split()
            if pid in pids:
                embed = helper_embed.invalid_embed(pid, "PID already in file")
            else:
                api_response = session.get(f"https://api.currys.co.uk/store/api/products/{pid}", timeout=30)
                if api_response.status_code == 200:
                    print(Fore.GREEN + f"[{now()}] [HELPER] {ctx.author.display_name} ADD COMPLETED: {pid}")
                    product_data = api_response.json()["payload"][0]
                    title = product_data["label"]
                    img_url = product_data["images"][0]["url"]
                    price = product_data["price"]["amount"]
                    pids.append(pid)
                    upload_pids_ftp(pids)
                    embed = helper_embed.base_embed(GREEN, title)
                    embed.add_field(name="Successfully Added:", value=pid, inline=True)
                    embed.add_field(name="Price", value=f"£{price/100}", inline=True)
                    embed.set_thumbnail(url=img_url)
                elif api_response.status_code == 404:
                    embed = helper_embed.invalid_embed(pid, "404 - Page not found")
                elif api_response.status_code == 403:
                    embed = helper_embed.invalid_embed(pid, "403 - Forbidden")
                else:
                    embed = helper_embed.invalid_embed(pid, f"{api_response.status_code} - Unknown Error")
        except (KeyError,IndexError):
            embed = helper_embed.invalid_embed(pid, "Failed to read JSON/Invalid product")
        except (requests.exceptions.ConnectTimeout, helheim.exceptions.HelheimSolveError):
            embed = helper_embed.invalid_embed(pid, "Timeout/Connection Error")

    await ctx.send(embed=embed)

@commands.dm_only()
@client.command()
async def remove(ctx, *, pids: list):
    pids = pids.split(" ")
    await ctx.send("Filtering out invalid PID(s)")
    pids = [pid for pid in pids if len(pid) == 8 and pid.isdigit()]
    if pids == []:
        await ctx.send("No valid PID(s) to remove")
    print(f"{Fore.CYAN}[{now()}] [HELPER] ATTEMPTING TO REMOVE: {pids}")
    stored_pids = requests.get("pids.txt", timeout=30).text.split()
    stored_pids_set = set(stored_pids) #A
    to_remove_set = set(pids) # B
    intersect = stored_pids_set.intersection(to_remove_set)
    if intersect: # A n B
        stored_pids = list(stored_pids_set - to_remove_set) # these are Pids to upload back into pids.txt A n B'
        upload_pids_ftp(stored_pids)    
        removed = "\n".join([f"[{i}](https://www.currys.co.uk/GBUK/product-{i}-pdt.html)" for i in intersect])
        success_embed = discord.Embed(title="Successfully Removed", color=GREEN)
        success_embed.set_footer(text=f"By Jheels | Requested by {ctx.author.display_name}")
        success_embed.set_author(name="Currys Helper")
        success_embed.add_field(name="PID(s)", value=removed)

        await ctx.send(embed=success_embed)

    not_in_file = to_remove_set - stored_pids_set # pids that do not exist in the file A' n B
    if len(not_in_file) != 0:
        failed_embed = discord.Embed(title="Failure!", color=RED)
        failed_embed.set_footer(text=f"By Jheels | Requested by {ctx.author.display_name}")
        failed_embed.set_author(name="Currys Helper")
        not_in_file = " \n".join([f"[{i}](https://www.currys.co.uk/GBUK/product-{i}-pdt.html)" for i in not_in_file])
        failed_embed.add_field(name="PID(s):", value=not_in_file)
        failed_embed.add_field(name="Reason:", value="These PID(s) do not exist in the file")
        await ctx.send(embed=failed_embed)

@commands.dm_only()
@client.command()
async def clear(ctx):
    embed = discord.Embed(title="Confirm to clear all PID(s) - [Y, N]", color=BLUE, timestamp=datetime.utcnow())
    await ctx.send(embed=embed)
    confirmation = await client.wait_for("message", timeout=30)
    while confirmation.content.upper() not in ["Y","N"]:
        if confirmation.content[0] == "!":
            return None 
        await ctx.send("Invalid input - try again")
        confirmation = await client.wait_for("message", timeout=30)
    if confirmation.content.upper() == "Y":
        await ctx.send("Clearing all PID(s)!")
        upload_pids_ftp(pids=[])
        await ctx.send("Succesfully cleared PID(s)")


client.run("")
