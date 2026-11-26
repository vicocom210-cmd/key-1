# Cheat report: modified PUBG MOBILE 4.7.0 iOS IPA ("VNHAX iOS Global REUPDATE v1")

**Prepared for:** PUBG MOBILE / Krafton / Tencent anti-cheat security team
**Date of analysis:** 2026-11-26
**Method:** static analysis only (file was never installed or executed)

## 1. Summary

A modified PUBG MOBILE 4.7.0 (Global, `com.tencent.ig`, build 21730) IPA is being distributed on Telegram
together with paid license keys. The game binary was patched to load an injected library
(`CheckNewDylib.framework`). That library drives a second, disguised library
(`AccessibilityUtilities.framework`) that contains the **VNHAX** cheat: ESP/wallhack, skeletons, radar, skin changer
and an "Anti Screen" mode that hides the cheat from screen recording. The cheat verifies a paid key against the
PHP license server **`http://www.vnhgaming.com/ac.php`** (behind Cloudflare), binds the key to the device ("machine code")
and keeps it alive with heartbeats.
The IPA also carries hidden, gzip-compressed copies of the **original encrypted game binary**, the **original
anti-cheat library (`anogs`)** and the original `Info.plist`/code-signature data. These copies are most likely
used to present "clean" files to integrity checks.

## 2. Distribution

| Item | Value |
|---|---|
| Telegram channel | "PUBG IOS HACK STORE" (~2,665 subscribers) |
| Key seller | Telegram account `@BlackCatOwner` ("BUY KEYS NOW") |
| Posted files | `PUBG MOBILE_4.7.0_1794661237.ipa` (Global, 3617.5 MB) and `PUBG MOBILE_4.7.0_1794662115.ipa` (Korea, 3624.2 MB) |
| Post text | "VNHAX IOS Global REUPDATE v1 / Build 1 / Ver: 1.0.1 / Name: Global-REL- r1 4.7" |
| In-game overlay seen in gameplay video | `VER: 1.0.1 / BUILD: 1 / APP: GL-REL r1 4.7`, `ANTIBAN STATUS: ONLINE` |

A related but separate seller, "PUBGxMODS™" (~16,182 subscribers, plus "PUBGxMODS GC" and "PUBGxMODS REVIEW"),
sells an ESP/visual cheat for GL/KR/TW/VNG/FLASH/BGMI 4.7.0. Its key screen (`PUBGxMODS 4.6 || PBC WH 64BIT`,
"MAX DEVICE REACHED") is **not** contained in this IPA and needs a separate sample.

## 3. File identification (SHA-256)

| File | SHA-256 |
|---|---|
| `PUBG MOBILE_4.7.0_1794661237.ipa` (3,793,268,966 bytes) | `d1b6dbd27dbab609174a66302c931ce7605b3db8682292f781b68883e08c34f8` |
| `Payload/ShadowTrackerExtra.app/ShadowTrackerExtra` (patched, decrypted) | `f8b64fbe6c1c3f9e001a73208b71f7cc380efa6b8895592584e5a663393489b3` |
| `Frameworks/CheckNewDylib.framework/CheckNewDylib` (loader) | `9e7edfcb07641f320230185ec4a61746216485e1b79513fe0297d43ec8ebce7d` |
| `Frameworks/AccessibilityUtilities.framework/AccessibilityUtilities` (VNHAX cheat, 17.5 MB) | `efe8f2a5022fec52ca1565d255532dedf97b9905e0a56a6499b1732e031e1f56` |
| `AccessibilityUtilities.framework/_stl_a.gz` (original encrypted game binary) | `45b71b2bdc225b4739b52af9b9a620837894cf8f8a9b895b686b3e76502d8343` |
| `AccessibilityUtilities.framework/_stl_b.gz` (original `anogs` anti-cheat library) | `b893a6c62a1a1fee5befa40ad710c9bc064c39dac82f271ab3de4f42fb1f83c6` |
| `AccessibilityUtilities.framework/_stl_c.gz` (original Info.plist) | `19e070d1b774f93a61bcbaf67ceab69c91257dbae9edc3ce942e499fc2192735` |
| `AccessibilityUtilities.framework/_stl_d.gz` (original signature plist) | `5d6a5a88850c32e8516dd84e9a0ade68d3cd97959dbee50124d31c2f6f55847b` |

## 4. How the cheat is injected

1. **Patched main binary.** `ShadowTrackerExtra` is decrypted (`cryptid=0`) and has an extra load command
   `LC_LOAD_DYLIB @rpath/CheckNewDylib.framework/CheckNewDylib`. It is placed just before the legitimate
   `@rpath/anogs.framework/anogs`, so the loader runs before the anti-cheat initializes.
2. **Loader: `CheckNewDylib.framework`** (86 KB). Bundle ID `com.xxx.app.CheckNewDylib`, built with Xcode 26.2 / iOS SDK 26.2.
3. **Cheat: `AccessibilityUtilities.framework`**. It is named after a real Apple private framework to look legitimate.
   Fake bundle ID `com.app.apple.AccessibilityUtilities`. It is not referenced by the main binary, so it is loaded
   at runtime by the loader. Its files are dated 2026-11-10 and 2026-11-13, while the original game files are dated 2026-11-02.
4. **Hidden originals.** `_stl_a.gz` decompresses to the original **encrypted** (`cryptid=1`) game executable,
   byte-size identical to the patched one (188,963,856 bytes). `_stl_b.gz` is an `anogs` build (it contains strings such as
   "Your device has been jailbroken…", `_AnoSDKSetUserInfoWithLicense`). `_stl_c.gz` and `_stl_d.gz` are the original plists.

## 5. License / key system (inside `AccessibilityUtilities`)

A C++ class `Verify` implements a network license check:

`verifyInit`, `login`, `callPHP`, `getParaEx`, `retCode`, `bindMachineCode`, `setUserbind`, `heartbeat`,
`addBlackList`, `getDeviceInfo`, `getSystemInfo`, `deviceIPAddress`, `getClientVersion`, `saveUserPassword`,
`loadPass`, `aes…`, `getStrMd5`, `CodefilePath`, `DylibPath`, `AppNamePath`, `removefile`, and a free function `verifyPost`.

- **Server type:** PHP endpoint (`callPHP`). Requests are sent as `application/x-www-form-urlencoded` / JSON over a
  custom HTTP client (`nttPost`, raw sockets, a manually built `Host:` header). AFNetworking with SSL public-key pinning
  and RSA-SHA256 signature verification (`SecKeyVerifySignature`) is also linked.
- **Data sent:** key/password, device "machine code" (from `getDeviceInfo`/`UIDevice`), system info, client version,
  device IP address. `addBlackList` suggests that the server can ban devices or keys.
- **Device binding and heartbeat:** `bindMachineCode` ties a key to a device, and `heartbeat` re-validates it periodically.
  User-facing strings include "License expires", "Reset Key", "Reset Device", "Key reset done. Restart and login again.".
- **License server (recovered):**

  ```
  http://www.vnhgaming.com/ac.php?s=2f5c45b6818a56d5382fb8f34907a6b7
  ```

  The URL is stored AES-256-CBC-encrypted in `Verify::verifyInit`. The AES key and IV are themselves hidden as
  XOR-obfuscated stack strings (the `xorstr` technique). They were recovered by emulating the function (Unicorn) and decrypting
  the blobs offline. The same routine also holds a client ID and response-signing values. They are intentionally
  left out of this report and can be provided to the PUBG security team on request.
  The traffic is **plain HTTP**: keys, passwords and device data are sent unencrypted at the transport level.
- **Hosting:** `www.vnhgaming.com` sits behind **Cloudflare** (NS `olga.ns.cloudflare.com` / `anton.ns.cloudflare.com`;
  A records 104.26.2.238, 104.26.3.238, 172.67.68.134). The origin server is hidden.
- **Request formats (POST body, decoded from the binary):**

  | Function | Body |
  |---|---|
  | `verifyInit` | `action=init` (+ `clientID`) |
  | `login` | `action=login&user=…&pwd=…&code=…&client_version=…` |
  | `heartbeat` | `action=heartbeat&user=…&auth=…` |
  | `bindMachineCode` | `action=bind&user=…` |
  | `setUserbind` | `action=bindstr&user=…&pwd=…&str=…` |
  | `addBlackList` | `action=addBlacklist&code=…&remark=…` |
  | `callPHP` | `action=callPHP&fun=…&para=…&user=…` |

- **Device data collected (`getSystemInfo`):** reads `/System/Library/CoreServices/SystemVersion.plist`, `deviceName`,
  `systemVersion`, `deviceModel`, `uuidString`, `bluetoothAddress`. The key is stored locally in `Code.txt`.

The UI strings are partly Vietnamese, which matches the "VN" in "VNHAX".

## 6. Cheat features (from UI strings)

ESP / wallhack, skeletons, player info, rear indicators, radar (position and size), skin changer ("Skin Mode",
"Start Skins", weapon and pet skin targets), an "Anti Screen" / "Screen privacy" mode that hides the overlay from
recordings, and an ImGui-based menu (`VNHAX##layout`).

## 7. Code signing

| Item | Value |
|---|---|
| Re-signing tool | eSign (`SignedByEsign` marker file, "Signed By Esign", `https://esign.yyyue.xyz`) |
| Certificate | `Apple Distribution: jianbao liu (L648X4K55W)` |
| Team ID | `L648X4K55W` |
| App ID | `L648X4K55W.app.citrine1833.lapis9407` (AppIDName `Citrine1833Lapis9407 …`) |
| Profile | ad-hoc, 1 provisioned device, created 2026-11-09, expires 2027-10-26 |

The random App ID and the single-device profile match a commercial "UDID signing" service that re-sells a developer account.
**Team ID `L648X4K55W` should also be reported to Apple** so that the certificate can be revoked.

## 8. Recommended actions

- PUBG / anti-cheat: add detection for the injected `CheckNewDylib` and `AccessibilityUtilities` images, the
  `_stl_*.gz` side-files, and the hashes above. Investigate accounts that played on build 21730 with these modules loaded.
- PUBG / anti-cheat: flag game clients that contact `vnhgaming.com`.
- Cloudflare: abuse report for `vnhgaming.com` (license server for a paid game cheat that collects device identifiers).
- Apple: report developer Team ID `L648X4K55W` (certificate "jianbao liu") for distributing a modified third-party game.
- Telegram: report the channel "PUBG IOS HACK STORE" and the seller `@BlackCatOwner`.
