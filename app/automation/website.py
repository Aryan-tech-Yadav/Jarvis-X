import webbrowser

class WebsiteManager:
    
    def open(self, website):
        
        websites = {
            "google" : "https://www.google.com",
            "youtube" : "https://www.youtube.com",
            "instagram" : "https://www.instagram.com",
            "facebook" : "https://www.facebook.com",
            "twitter" : "https://www.twitter.com",
            "x" : "https://www.x.com",
            "github" : "https://www.github.com",
            "chatgpt" : "https://www.chatgpt.com",
            "gmail" : "https://www.gmail.com",
            "linkedin" : "https://www.linkedin.com",
            "reddit" : "https://www.reddit.com",
            "whatsapp" : "https://web.whatsapp.com",
            "netflix" : "https://www.netflix.com",
            "amazon" : "https://www.amazon.com",
            "flipkart" : "https://www.flipkart.com",
            "stackoverflow" : "https://stackoverflow.com",
            "chatgpt" : "https://chatgpt.com",
            "claude" : "https://claude.ai",
            "gemini" : "https://gemini.google.com",
            "bing" : "https://www.bing.com",
            "yahoo" : "https://www.yahoo.com",
            "maps" : "https://www.google.com/maps",
            "drive" : "https://drive.google.com",
            "docs" : "https://docs.google.com",
            "sheets" : "https://sheets.google.com",
            "slides" : "https://slides.google.com",
            "photos" : "https://photos.google.com",
            "calendar" : "https://calendar.google.com",
            "gmail" : "https://mail.google.com",
            "outlook" : "https://outlook.live.com",
            "teams" : "https://teams.microsoft.com",
            "zoom" : "https://zoom.us",
            "discord" : "https://discord.com",
            "telegram" : "https://web.telegram.org",
            "spotify" : "https://open.spotify.com",
            "soundcloud" : "https://soundcloud.com",
            "wikipedia" : "https://www.wikipedia.org",
            "quora" : "https://www.quora.com",
            "medium" : "https://medium.com",
            "dev" : "https://dev.to",
            "hackernews" : "https://news.ycombinator.com",
            "producthunt" : "https://www.producthunt.com",
            "dribbble" : "https://dribbble.com",
            "behance" : "https://www.behance.net",
            "figma" : "https://www.figma.com",
            "canva" : "https://www.canva.com",
            "trello" : "https://trello.com",
            "notion" : "https://www.notion.so",
            "slack" : "https://slack.com",
            "asana" : "https://asana.com",
            "jira" : "https://www.atlassian.com/software/jira",
            "confluence" : "https://www.atlassian.com/software/confluence",
            "wordpress" : "https://wordpress.com",
            "blogger" : "https://blogger.com",
            "tumblr" : "https://www.tumblr.com",
            "pinterest" : "https://www.pinterest.com",
            "tiktok" : "https://www.tiktok.com",
            "snapchat" : "https://www.snapchat.com",
            "twitch" : "https://www.twitch.tv",
            "disney" : "https://www.disneyplus.com",
            "hotstar" : "https://www.hotstar.com",
            "sonyliv" : "https://www.sonyliv.com",
            "jio" : "https://www.jio.com",
            "airtel" : "https://www.airtel.in",
            "bsnl" : "https://www.bsnl.co.in",
            "irctc" : "https://www.irctc.co.in",
            "paytm" : "https://paytm.com",
            "phonepe" : "https://phonepe.com",
            "gpay" : "https://pay.google.com",
            "amazonpay" : "https://pay.amazon.com",
            "cred" : "https://cred.club",
            "zomato" : "https://www.zomato.com",
            "swiggy" : "https://www.swiggy.com",
            "uber" : "https://www.uber.com",
            "ola" : "https://www.olacabs.com",
            "rapido" : "https://rapido.bike",
            "makemytrip" : "https://www.makemytrip.com",
            "goibibo" : "https://www.goibibo.com",
            "yatra" : "https://www.yatra.com",
            "booking" : "https://www.booking.com",
            "airbnb" : "https://www.airbnb.com",
            "justdial" : "https://www.justdial.com",
            "indiamart" : "https://www.indiamart.com",
        }
        
        site = website.lower().strip()
        
        # Direct match
        if site in websites:
            webbrowser.open(websites[site])
            return f"Opening {website}."
        
        # Partial match
        for key, url in websites.items():
            if key in site or site in key:
                webbrowser.open(url)
                return f"Opening {key}."
        
        # Try as URL
        if "." in site and not site.startswith("http"):
            webbrowser.open(f"https://{site}")
            return f"Opening {website}."
        
        # Google search fallback
        webbrowser.open(f"https://www.google.com/search?q={website.replace(' ', '+')}")
        return f"Searching for {website} on Google."
        