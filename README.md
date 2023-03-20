<a href="https://deepsource.io/gh/hikariatama/Hikka/?ref=repository-badge"><img src="https://deepsource.io/gh/hikariatama/Hikka.svg/?label=active+issues&show_trend=true&token=IPVI_QX-cSuQSVeVl8cb5PLt" alt="DeepSource"></a>
<a href="https://deepsource.io/gh/hikariatama/Hikka/?ref=repository-badge"><img src="https://deepsource.io/gh/hikariatama/Hikka.svg/?label=resolved+issues&show_trend=true&token=IPVI_QX-cSuQSVeVl8cb5PLt" alt="DeepSource"></a><br>
<a href="https://www.codacy.com/gh/hikariatama/Hikka/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=hikariatama/Hikka&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/97e3ea868f9344a5aa6e4d874f83db14"/></a>
<a href="#"><img src="https://img.shields.io/github/languages/code-size/hikariatama/Hikka"/></a>
<a href="#"><img src="https://img.shields.io/github/issues-raw/hikariatama/Hikka"/></a>
<a href="#"><img src="https://img.shields.io/github/license/hikariatama/Hikka"/></a>
<a href="#"><img src="https://img.shields.io/github/commit-activity/m/hikariatama/Hikka"/></a><br>
<a href="#"><img src="https://img.shields.io/github/forks/hikariatama/Hikka?style=flat"/></a>
<a href="#"><img src="https://img.shields.io/github/stars/hikariatama/Hikka"/></a>&nbsp;<a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a><br>

<hr>
<h2><img src="https://github.com/hikariatama/assets/raw/master/1326-command-window-line-flat.webp" height="54" align="middle"> Installation</h2>

### Installation page

<img src="https://github.com/hikariatama/assets/raw/master/install_qr.gif" height="256">

<a href="https://t.me/lavhostbot?start=SGlra2E"><img src="https://user-images.githubusercontent.com/36935426/167272288-85f00779-4b98-47da-8d0d-ea2c6370b979.png" height="40"></a>

<h2>Local installation:</h2>
Simply run this command out of <b>root</b> and follow the instructions of installer:<br>
<code>. <(wget -qO- https://hikariatama.ru/get_hikka)</code><br>
<br>
<b>Manual installation (no script):</b><br>
<code>apt update && apt install git libcairo2 -y && git clone https://github.com/hikariatama/Hikka && cd Hikka && pip install -r requirements.txt && python3 -m hikka</code><br.>
<i>If you are on VPS\VDS, type <code>--proxy-pass</code> in the end of command to open SSH tunnel to your Hikka web interface, or use <code>--no-web</code> to complete setup in console</i><br>
<br>
<b><a href="https://ide.goorm.io">Goorm</a> installation:</b><br>
<details>
 <summary>1. Go to https://ide.goorm.io, click <b>Sign Up</b></summary>
 <img src="https://img1.teletype.in/files/c1/0f/c10f7478-1878-4960-9c4e-91ac81c1fd15.png">
</details>
<details>
 <summary>2. Click <b>Skip</b></summary>
 <img src="https://img4.teletype.in/files/77/a5/77a57aa2-1671-4881-98a3-30aacaad6636.png">
</details>
<details>
 <summary>3. Click <b>New container</b></summary>
 <img src="https://img2.teletype.in/files/d9/b1/d9b18933-8b91-492b-bf36-b160ee0b6579.png">
</details>
<details>
 <summary>4. Press <b>Ctrl+M</b> or click the button <b>Create</b> in the end of page</summary>
 <img src="https://img3.teletype.in/files/a1/a8/a1a8e1e3-b6be-444e-be9b-4255e2bf9fa8.png">
</details>
<details>
 <summary>5. After the container is created, click <b>Stop</b></summary>
 <img src="https://img2.teletype.in/files/15/1b/151b0736-2948-45a4-b72b-adbe1c2b1761.png">
</details>
<details>
 <summary>6. Confirm with <b>Stop container</b></summary>
 <img src="https://img2.teletype.in/files/92/1b/921b17fb-a9d2-4ee7-82aa-14d2353999ca.png">
</details>
<details>
 <summary>7. Turn on <b>Always-on</b></summary>
 <img src="https://img1.teletype.in/files/c2/7a/c27ae24f-a9bd-433d-b13a-081ee16b38a9.png">
</details>
<details>
 <summary>8. Click <b>Run</b></summary>
 <img src="https://img4.teletype.in/files/3a/55/3a55f92d-c188-4769-9070-75e4d90c25d7.png">
</details>
<details>
 <summary>9. Paste the command from spoiler to terminal</summary>
 <code>export GOORM="1" && apt update -y && apt upgrade -y && apt install python3.8 git wget -y && git clone https://github.com/hikariatama/Hikka && (wget -qO- https://bootstrap.pypa.io/get-pip.py | python3.8 -) && update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1 && update-alternatives --set python /usr/bin/python3.8 && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && update-alternatives --set python3 /usr/bin/python3.8 && update-alternatives --set python /usr/bin/python3.8 && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && update-alternatives --set python3 /usr/bin/python3.8 && alias python3=/usr/bin/python3 && alias python=/usr/bin/python3 && alias pip="python3.8 -m pip" && alias pip3="python3.8 -m pip" && cd Hikka && python3.8 -m pip install -r requirements.txt && (python3.8 -m hikka &)</code>
 <img src="https://img1.teletype.in/files/c1/d5/c1d5035a-96ed-4c76-83ee-114becf0e2b3.png">
</details>
<details>
 <summary>10. Leave the container to do it's thing and be ready to type <code>2</code> following by <code>Enter</code> in terminal if the content from attached picture occures <b>Run</b></summary>
 <img src="https://img1.teletype.in/files/c6/36/c636e420-223b-4818-885e-1d60a17b840e.png">
</details>
<details>
 <summary>11. In the end you'll see the link. Follow it and fill in the required data</summary>
 <img src="https://img3.teletype.in/files/65/5f/655fb083-0e85-470d-8873-bb971a90b084.png">
 <img src="https://img3.teletype.in/files/ef/b1/efb1e78c-9134-4839-b23d-a46f6a4ddc58.png">
</details>

<b>Some further details:</b>

<details>
 <summary>Pre-installed automatic database backuper</summary>
 <img src="https://user-images.githubusercontent.com/36935426/202905566-964d2904-f3ce-4a14-8f05-0e7840e1b306.png" width="300">
</details>
<details>
 <summary>Welcome installation info</summary>
 <img src="https://user-images.githubusercontent.com/36935426/202905720-6319993b-697c-4b09-a194-209c110c79fd.png" width="300">
 <img src="https://user-images.githubusercontent.com/36935426/202905746-2a511129-0208-4581-bb27-7539bd7b53c9.png" width="300">
</details>

<hr>
<h2><img src="https://github.com/hikariatama/assets/raw/master/35-edit-flat.webp" height="54" align="middle"> Changes</h2>

<ul>
 <li>🆕 <b>Latest Telegram layer</b> with reactions, video stickers and other stuff</li>
 <li>🔓 <b>Security</b> improvements, including <b>native entity caching</b> and <b>targeted security rules</b></li>
 <li>🎨 <b>UI/UX</b> improvements</li>
 <li>📼 Improved and new <b>core modules</b></li>
 <li>⏱ Quick <b>bug fixes</b> (compared to official FTG and GeekTG)</li>
 <li>▶️ <b>Inline forms, galleries and lists</b></li>
 <li>🔁 Full <b>backward compatibility</b> with FTG, GeekTG and Dragon Userbot modules</li>
</ul>
<hr>
<h2 border="none"><img src="https://github.com/hikariatama/assets/raw/master/1312-micro-sd-card-flat.webp" height="54" align="middle"> Requirements</h2>
<ul>
 <li>Python 3.8+</li>
 <li>API_ID and HASH from <a href="https://my.telegram.org/apps" color="#2594cb">Telegram</a></li>
</ul>
<hr>
<h2 border="none"><img src="https://github.com/hikariatama/assets/raw/master/680-it-developer-flat.webp" height="54" align="middle"> Documentation</h2>

Check out <a href="https://github.com/hikariatama/Hikka/wiki">Wiki</a> for developers' documentation<br>
User docs will be available soon

<hr>
<h2 border="none"><img src="https://github.com/hikariatama/assets/raw/master/981-consultation-flat.webp" height="54" align="middle"> <a href="https://t.me/hikka_talks">Support</a></h2>
<hr>
<h2 border="none"><img src="https://github.com/hikariatama/assets/raw/master/541-hand-washing-step-12-flat.webp" height="54" align="middle"> Features</h2>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1286-three-3-key-flat.webp" height="32" align="middle"><b> Forms - bored of writing? Use buttons!</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/61-camera-flat.webp" height="32" align="middle"><b> Galleries - scroll your favorite photos in Telegram</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/202842205-9a3906f8-37b1-47f4-acd1-ae441f84aeab.gif">
  </td>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/202842215-b7bddaf2-f544-4823-80b4-5c2cccaf2157.gif">
  </td>
 </tr>
</table>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/216-arrow-5-flat.webp" height="32" align="middle"><b> Inline - share userbot with your friends</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1054-amazon-echo-speaker-flat.webp" height="32" align="middle"><b> Bot interactions - "No PM"? No problem. Feedback bot at your service</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/202842234-e53f616d-7423-4a64-a5da-fb71282ad2c4.gif">
  </td>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/160476037-9537f1c7-8b72-408f-b84c-b89825930bf5.gif">
  </td>
 </tr>
</table>
<table>
 <tr>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/1140-error-flat.webp" height="32" align="middle"><b> InlineLogs - traceback directly in message, caused error</b>
  </td>
  <td>
   <img src="https://github.com/hikariatama/assets/raw/master/35-edit-flat.webp" height="32" align="middle"><b> Grep - execute command and get only required lines</b>
  </td>
 </tr>
 <tr>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/202842250-b60d218e-9df4-47f6-8c67-b2ef641b4d2d.gif">
  </td>
  <td>
   <img src="https://user-images.githubusercontent.com/36935426/202842263-ee2d5c94-3fd5-43b3-b8ac-2397b69e0fc6.gif">
  </td>
 </tr>
</table>

<b>👨‍👦 NoNick, NoNickUser, NoNickCmd, NoNickChat - use another account for userbot</b>
<img src="https://user-images.githubusercontent.com/36935426/202842278-37fbc518-1679-45d7-92f5-9e519275630d.png">

<hr>
<i>⚠️ This project is provided as-is. Developer doesn't take ANY responsibility over any problems, caused by userbot. By installing Hikka you take all risks on you. This is but not limited to account bans, deleted (by Telegram algorithms) messages, SCAM-modules, leaked sessions (due to SCAM-modules). It is <b>highly</b> recommended to enable the API Flood protection (.api_fw_protection) and not to install many modules at once. By using Hikka you give your consent to any actions made by your account in background in purposes of automatization. Please, consider reading https://core.telegram.org/api/terms for more information.</i>

<b>Special thanks to:</b>

<ul>
    <li><a href="https://gitlab.com/hackintosh5">Hackintosh5</a> for FTG, which is the base of project</li>
    <li><a href="https://t.me/kazunimo">Kazunimo</a> for Turkish translation pack</li>
    <li><a href="https://t.me/hegaNET">Hegakura</a> for Tatar translation pack</li>
    <li><a href="https://t.me/tiefeschwarz">Aldehydesäure</a> for German translation pack</li>
    <li><a href="https://t.me/amorescam">Amore</a> for Uzbek translation pack</li>
    <li><a href="https://t.me/lonami">Lonami</a> for Telethon, which is the base of Hikka-TL</li>
    <li><a href="https://github.com/delivrance">Dan</a> for pyrogram, which is the base of Hikka-Pyro</li>
</ul>
