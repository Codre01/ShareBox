# **SHAREBOX**

# **Master Product & Technical Specification**

**Document Version:** 1.0  
**Product:** ShareBox  
**Initial Release Target:** Windows  
**Architecture Target:** Windows, macOS, Linux  
**Distribution Model:** Open Source  
**Document Audience:** Design AI, Code AI, human developers and contributors  
**Status:** V1 Specification 

# **1\. Document Overview**

## **1.1 Purpose**

This document defines the product, user experience, functional requirements, architecture, security model, technical behaviour and implementation requirements for **ShareBox**.

It is the primary source of truth for the project.

A Design AI should be able to use this document to design the complete ShareBox interface and all required states.

A Code AI or developer should be able to use it to implement ShareBox without independently redefining the product architecture, workflows or core behaviour.

Where implementation choices are not explicitly specified, they must preserve the product principles and requirements established in this document.

---

## **1.2 Requirement Language**

Requirements use three priority levels:

**MUST** — mandatory. The implementation is incomplete or incorrect without it.

**SHOULD** — expected behaviour. It may only be changed where there is a justified technical, security or platform-specific reason.

**MAY** — optional behaviour or implementation detail.

---

## **1.3 Product Decisions Already Locked**

The following decisions are authoritative:

* Product name is **ShareBox**.  
* ShareBox transfers files over the local network.  
* Internet connectivity is not required for core functionality.  
* A desktop computer acts as the ShareBox host.  
* The host runs an installed desktop application.  
* Other devices access ShareBox through a standard web browser.  
* Mobile applications are not required.  
* Users interact with shared files through a normal folder on the host computer.  
* Browser clients can upload and download files.  
* Browser clients cannot delete or rename host files in V1.  
* Subfolders are supported.  
* New devices are paired using a QR-based flow.  
* Trusted devices are remembered.  
* Trusted devices automatically reconnect when possible.  
* Trusted devices can be revoked from the desktop application.  
* Each uploading device receives its own automatically created subfolder.  
* Device folders are created only after the device uploads its first item.  
* ShareBox is architected cross-platform.  
* Windows is the first implementation and release target.  
* macOS and Linux follow after Windows V1 is stable.  
* ShareBox is an open-source project.

---

# **2\. Product Overview**

## **2.1 Product Definition**

ShareBox is a local-network file sharing utility that provides a simple shared space between a user's computer and other devices on the same network.

The host computer runs ShareBox and exposes a designated local folder to authorized devices through a browser-based interface.

A user can place a file into the ShareBox folder on their computer and immediately access it from an authorized phone, tablet or computer connected to the same local network.

Authorized devices can also upload files back to the host computer.

No cloud storage, messaging application, email service, USB cable or internet connection is required.

---

# **3\. Problem Statement**

Moving small files between personal devices is unnecessarily cumbersome, particularly across different operating-system ecosystems.

A common example is:

1. User takes a screenshot on a Windows computer.  
2. User needs the screenshot on an iPhone or Android device.  
3. Existing workflows may require:  
   * sending the image through WhatsApp or another messaging platform;  
   * emailing it;  
   * uploading it to cloud storage;  
   * connecting a USB cable;  
   * using Bluetooth;  
   * opening a third-party transfer application on multiple devices.

These workflows introduce unnecessary steps and may depend on internet connectivity even though both devices are physically connected to the same local network.

The underlying requirement is simpler:

> A file available on one personal device should be easily accessible from another personal device on the same local network.

ShareBox addresses this requirement directly.

---

# **4\. Proposed Solution**

ShareBox turns the host computer into a lightweight private file hub on the local network.

The system consists of three primary user-facing components:

### **4.1 ShareBox Desktop Application**

An installed application on the host computer responsible for:

* running the ShareBox service;  
* selecting and managing the shared folder;  
* displaying service/network status;  
* pairing new devices;  
* managing trusted devices;  
* configuring ShareBox;  
* starting and stopping sharing;  
* handling operating-system integration.

### **4.2 ShareBox Folder**

A normal filesystem folder on the host computer.

Example on Windows:

C:\\Users\\John\\ShareBox\\

Files placed here become available to authorized browser clients.

The user does not need to import files into ShareBox through the desktop application's UI.

The operating system's normal file manager remains the primary host-side file-management interface.

### **4.3 ShareBox Web Client**

A responsive web application served directly by the ShareBox host.

Authorized devices on the same network open this interface using their browser.

The web client provides:

* folder navigation;  
* file browsing;  
* search;  
* previews where supported;  
* downloads;  
* uploads.

No ShareBox application needs to be installed on client devices.

---

# **5\. Product Mental Model**

ShareBox should feel like:

> **A folder on my computer that my devices can access when they are nearby.**

It should not feel like:

> **A server that I need to administer.**

Users should not normally need to understand:

* ports;  
* IP addresses;  
* HTTP servers;  
* network interfaces;  
* Python;  
* APIs;  
* mDNS;  
* firewall rules.

These are implementation concerns and should be abstracted wherever practical.

---

# **6\. Product Philosophy**

## **6.1 Local First**

Files MUST travel directly across the local network.

The core file-transfer workflow MUST NOT depend on an external server.

Internet access MUST NOT be required to:

* browse files;  
* upload files;  
* download files;  
* authenticate an already supported local connection;  
* use ShareBox normally.

---

## **6.2 Host-Owned**

The host computer is the source of truth.

ShareBox is not a distributed synchronization service.

Files are stored on the host filesystem.

Client devices access or contribute files to that filesystem through ShareBox.

---

## **6.3 Browser Universalism**

ShareBox SHOULD avoid requiring native applications on client devices.

A standards-compliant modern browser should be sufficient.

This enables interoperability across:

* iOS;  
* Android;  
* Windows;  
* macOS;  
* Linux;  
* tablets;  
* other browser-capable devices.

---

## **6.4 Low Friction**

Routine transfers should require as few deliberate actions as possible.

After initial pairing:

**Host → Phone**

Place file in ShareBox  
        ↓  
Open ShareBox bookmark on phone  
        ↓  
Download file

**Phone → Host**

Open ShareBox  
        ↓  
Upload file  
        ↓  
File appears on host

No repeated pairing should be required for trusted devices.

---

## **6.5 Secure by Default**

Being connected to the same Wi-Fi network MUST NOT automatically grant access to ShareBox.

Unknown devices must not be able to browse or download files merely by discovering the host.

Access requires authorization.

---

## **6.6 Invisible When Not Needed**

ShareBox SHOULD normally run quietly in the background.

The desktop application is primarily a control center rather than the user's primary file manager.

---

# **7\. Goals**

ShareBox V1 MUST provide a reliable way to:

* expose a host folder to authorized LAN devices;  
* browse that folder from a browser;  
* navigate subfolders;  
* download files;  
* upload files;  
* organize client-originated uploads by device;  
* securely pair devices;  
* remember trusted devices;  
* revoke trusted devices;  
* function without internet access;  
* run unobtrusively on the host;  
* provide a distributable Windows application.

ShareBox SHOULD make the experience understandable without technical networking knowledge.

---

# **8\. V1 Non-Goals**

The following are explicitly outside V1 scope:

* cloud storage;  
* internet-based remote file access;  
* user accounts;  
* ShareBox cloud services;  
* file synchronization across computers;  
* native iOS application;  
* native Android application;  
* browser-side file deletion;  
* browser-side file renaming;  
* browser-side file moving;  
* collaborative editing;  
* version history;  
* clipboard synchronization;  
* link/text sharing;  
* peer-to-peer client-to-client transfer;  
* public internet file sharing;  
* automatic backups.

Some may be considered in future versions.

They MUST NOT complicate the V1 architecture unnecessarily.

---

# **9\. Primary Use Cases**

## **9.1 Host Computer → Phone**

Example:

A user takes a screenshot on their PC.

They save or move it into ShareBox.

ShareBox/  
└── Screenshot.png

The user opens ShareBox from their phone.

The file appears.

They tap the file and download it.

---

## **9.2 Phone → Host Computer**

The user opens ShareBox on their phone and selects Upload.

They choose:

IMG\_2381.jpeg

If the phone is registered as:

**Bolu's iPhone**

ShareBox creates, if necessary:

ShareBox/  
└── Bolu's iPhone/  
    └── IMG\_2381.jpeg

The file immediately becomes available through the host filesystem.

---

# **10\. Per-Device Folder Model**

Client-originated content MUST be associated with its source device.

Each trusted device receives a filesystem-safe device identifier and display name.

Example:

ShareBox/  
├── Project.pdf  
├── Screenshot.png  
│  
├── Bolu's iPhone/  
│   ├── IMG\_2381.jpeg  
│   └── IMG\_2382.jpeg  
│  
└── Pixel 10/  
    └── recording.mp4

## **10.1 Lazy Folder Creation**

Pairing a device MUST NOT automatically create a folder.

Example:

Trusted Devices  
├── Bolu's iPhone  
├── iPad  
└── Pixel 10

If only Bolu's iPhone has uploaded something, the filesystem may contain:

ShareBox/  
└── Bolu's iPhone/

There MUST NOT be empty `iPad/` and `Pixel 10/` folders merely because those devices are trusted.

The folder is created upon the first successful upload requiring storage.

---

## **10.2 Device Folder Identity**

Internal device identity MUST NOT rely solely on the editable display name.

Renaming a trusted device in ShareBox must not accidentally cause it to impersonate another device or gain access to another device's internal identity.

Folder-name collisions MUST be handled safely.

---

# **11\. File Visibility Model**

Authorized devices may browse the entire ShareBox shared directory unless future permissions explicitly restrict this.

Therefore:

ShareBox/  
├── Screenshot.png  
├── Documents/  
│   └── Proposal.pdf  
├── Bolu's iPhone/  
│   └── Photo.jpeg  
└── Pixel/  
    └── Video.mp4

is visible through the browser as a navigable hierarchy.

Device-specific folders organize **uploads**; they do not represent private storage inaccessible to other trusted devices.

---

# **12\. Client Permissions**

V1 browser clients have deliberately limited filesystem privileges.

They MAY:

* browse;  
* navigate folders;  
* search;  
* preview supported files;  
* download;  
* upload.

They MUST NOT:

* delete;  
* rename;  
* move;  
* overwrite arbitrary existing files;  
* create arbitrary host-side directory structures unless specifically required by the upload implementation;  
* modify host files.

Host filesystem management remains the responsibility of the host user through Finder/File Explorer/etc.

---

# **13\. System Architecture**

At a high level:

                   HOST COMPUTER  
┌────────────────────────────────────────────────┐  
│                                                │  
│  ShareBox Desktop Application                  │  
│        │                                       │  
│        ├── Configuration                       │  
│        ├── Device Management                   │  
│        ├── Pairing                             │  
│        ├── Network Management                  │  
│        └── Local Server                        │  
│                    │                           │  
│                    ▼                           │  
│             ShareBox Backend                   │  
│                    │                           │  
│             ┌──────┴──────┐                    │  
│             │             │                    │  
│             ▼             ▼                    │  
│         Web Client    Shared Folder            │  
│                       C:\\...\\ShareBox           │  
│                                                │  
└───────────────────────┬────────────────────────┘  
                        │  
                  Local Network  
                        │  
          ┌─────────────┼─────────────┐  
          │             │             │  
          ▼             ▼             ▼  
       iPhone        Android       Laptop  
       Browser       Browser       Browser

---

# **14\. Host and Client Roles**

## **14.1 Host**

The computer running the ShareBox desktop application.

There is one authoritative host per ShareBox instance.

The host:

* stores files;  
* serves the web application;  
* authenticates devices;  
* receives uploads;  
* provides downloads;  
* manages trusted devices.

## **14.2 Client**

Any authorized browser-capable device accessing the host.

A client does not need ShareBox installed.

---

# **15\. Desktop Application Responsibilities**

The desktop application MUST provide:

* ShareBox service status;  
* start/stop sharing;  
* shared-folder selection;  
* open shared folder;  
* pairing controls;  
* QR code;  
* connection address;  
* trusted-device management;  
* device revocation;  
* network status;  
* application settings;  
* launch-at-startup setting;  
* access to relevant errors.

The desktop application SHOULD remain small and focused.

It MUST NOT duplicate a full file manager.

---

# **16\. Desktop Application States**

The application must account for at least:

### **Running**

ShareBox is operational and reachable.

● ShareBox is running

### **Stopped**

The local server is intentionally stopped.

○ Sharing is off

### **Network unavailable**

ShareBox is running locally but no usable LAN connection exists.

\! No local network detected

### **Configuration error**

Example:

Shared folder no longer exists.

### **Port/network error**

ShareBox cannot start its service.

### **Pairing mode**

A temporary pairing opportunity is active.

Each state must communicate:

1. what is happening;  
2. whether ShareBox is usable;  
3. what the user needs to do, if anything.

---

# **17\. System Tray Behaviour**

ShareBox SHOULD run in the system tray on Windows.

Closing the main window SHOULD normally minimize/hide the control interface rather than terminate the ShareBox service.

The tray menu SHOULD expose quick actions such as:

ShareBox  
──────────────  
Open ShareBox  
Open Folder  
Sharing: On  
Pair Device  
──────────────  
Quit

The distinction between **closing the window** and **quitting ShareBox** must be clear.

---

# **18\. Startup Behaviour**

ShareBox SHOULD provide:

> Launch ShareBox when my computer starts

When enabled:

1. operating system starts;  
2. ShareBox launches in the background;  
3. server initializes;  
4. configured shared folder becomes available;  
5. trusted devices may reconnect.

The main ShareBox window SHOULD NOT automatically appear on every system boot unless user action is required.

---

# **19\. Shared Folder**

On first setup, ShareBox MUST either:

* create a sensible default ShareBox folder; or  
* allow the user to select an existing folder.

Recommended Windows default:

%USERPROFILE%\\ShareBox

The user MUST be able to change the shared folder later.

ShareBox MUST clearly warn about the implications of exposing a folder containing sensitive files.

---

# **20\. Filesystem Behaviour**

ShareBox MUST reflect actual filesystem state.

If a host user:

* adds a file;  
* deletes a file;  
* renames a file;  
* creates a folder;  
* moves a file;

the browser should reflect the new state without requiring ShareBox to maintain a duplicate file database.

The filesystem is authoritative.

Metadata databases MAY be used for ShareBox-specific information but MUST NOT become the canonical record of which files exist.

---

# **21\. Subfolder Navigation**

Subfolders MUST be supported.

Example browser navigation:

ShareBox  
   \>  
Projects  
   \>  
Glide

The user must be able to:

* enter folders;  
* return to parent folders;  
* return to root;  
* understand their current location.

Breadcrumb navigation SHOULD be used on larger displays.

Mobile navigation MAY use a simplified equivalent where necessary.

---

# **22\. Upload Behaviour**

Uploads MUST be streamed to disk where practical.

Large files MUST NOT require the entire file to be held in memory.

An upload MUST show:

* filename;  
* progress;  
* completion;  
* failure.

Users SHOULD be able to select multiple files in one upload action.

Drag-and-drop upload SHOULD be supported on compatible desktop browsers.

---

# **23\. Upload Destination**

Uploads from a client are stored under that client's device folder.

For device:

Bolu's iPhone

the upload root is:

ShareBox/Bolu's iPhone/

This rule applies regardless of which host folder the client is currently browsing.

This prevents client uploads from being mixed unpredictably with host-created content.

Future versions may expand the model, but V1 MUST maintain predictable device-originated storage.

---

# **24\. Filename Collisions**

ShareBox MUST NOT silently destroy an existing file.

If:

IMG\_1001.jpeg

already exists and another file with the same name is uploaded, ShareBox SHOULD generate a non-destructive alternative such as:

IMG\_1001 (1).jpeg

then:

IMG\_1001 (2).jpeg

The original file MUST remain unchanged.

---

# **25\. Download Behaviour**

Files SHOULD be streamed from disk rather than loaded entirely into application memory.

Downloads MUST support files substantially larger than available application RAM.

The server SHOULD use appropriate headers so browsers can:

* determine filenames;  
* determine content types where possible;  
* determine content length where practical;  
* download efficiently.

---

# **26\. Web Client**

The ShareBox web client is the primary interface for non-host devices.

It MUST be:

* mobile-first;  
* responsive;  
* touch-friendly;  
* fast;  
* usable on modern Safari;  
* usable on modern Chrome;  
* usable on Chromium-based browsers;  
* functional without internet connectivity.

Its frontend assets MUST be served locally by ShareBox.

No essential CSS, JavaScript, fonts, icons or runtime dependencies may require an external CDN.

---

# **27\. Web Client Information Architecture**

The primary interface should emphasize:

### **Header**

* ShareBox identity;  
* host/device connection state where useful.

### **File area**

* folders;  
* files;  
* search;  
* relevant metadata;  
* download actions.

### **Upload action**

A prominent upload control.

Secondary technical information should not dominate the interface.

---

# **28\. File Representation**

Each item SHOULD communicate enough information to identify it quickly.

Depending on viewport and file type:

* filename;  
* file/folder icon or thumbnail;  
* file type;  
* file size;  
* modification time;  
* download action.

The UI SHOULD prioritize filename and recognizable visual identity over excessive metadata.

---

# **29\. File Preview**

V1 SHOULD provide previews where browser support makes this straightforward.

Priority:

* images;  
* PDF;  
* video;  
* audio;  
* plain text where safe.

Unknown or unsupported formats should remain downloadable.

ShareBox MUST NOT attempt to implement specialized viewers for every possible format.

---

# **30\. Search**

Search MUST allow the user to locate files by filename.

V1 search SHOULD operate against the current ShareBox filesystem rather than requiring a complex persistent search index.

Search behaviour must remain responsive for reasonable personal-use directory sizes.

---

# **31\. Pairing Model**

Possession of the ShareBox URL alone MUST NOT permanently authorize a new device.

Initial device access requires pairing.

Recommended workflow:

Desktop  
   ↓  
Pair New Device  
   ↓  
Temporary QR code  
   ↓  
Phone scans QR  
   ↓  
Pairing request  
   ↓  
Authorization established  
   ↓  
Device becomes trusted

The QR code MUST contain sufficient information for the device to locate and securely participate in the pairing process.

Sensitive long-lived credentials SHOULD NOT be unnecessarily exposed in reusable QR codes.

Pairing credentials MUST expire.

---

# **32\. Trusted Devices**

Successful pairing creates a trusted-device record.

A trusted device SHOULD contain at minimum:

* unique internal device ID;  
* display name;  
* authorization credential information;  
* first paired timestamp;  
* last seen timestamp where available.

Trusted-device authentication MUST NOT depend on IP address.

IP addresses can change frequently and are not device identities.

---

# **33\. Automatic Reconnection**

Once trusted, a device SHOULD reconnect without requiring a new QR scan each time.

Expected experience:

User comes home  
     ↓  
Phone joins same Wi-Fi as PC  
     ↓  
User opens saved ShareBox bookmark  
     ↓  
ShareBox recognizes trusted device  
     ↓  
Files are available

No approval prompt should appear during normal trusted reconnection.

---

# **34\. Device Revocation**

The desktop application MUST list trusted devices.

The host user MUST be able to revoke a device.

Revocation MUST invalidate that device's authorization credentials.

After revocation, the device must be treated as unknown and must pair again before accessing files.

Revoking a device MUST NOT automatically delete files previously uploaded by that device.

---

# **35\. Device Naming**

During or immediately after pairing, ShareBox SHOULD establish a human-readable device name.

Examples:

* Bolu's iPhone  
* Samsung S25  
* iPad  
* Office Laptop

Because browsers may not reliably expose precise hardware identity, ShareBox MUST NOT depend on automatic hardware-name detection.

A suggested name MAY be generated, but users must be able to identify and rename trusted devices from the host.

---

# **36\. Network Model**

ShareBox operates primarily within a LAN.

Supported scenarios SHOULD include:

PC ── Wi-Fi Router ── Phone

and:

PC ── Phone Hotspot ── Phone

and other normal configurations where the devices can directly reach one another.

ShareBox does not guarantee operation on networks that intentionally isolate clients.

Examples include some:

* hotel networks;  
* corporate networks;  
* guest Wi-Fi systems;  
* university networks;  
* public hotspots.

The UI should distinguish a ShareBox failure from network-level client isolation where reasonably detectable.

---

# **37\. Internet Independence**

Once installed, ShareBox's core functionality MUST remain operational if:

Internet \= unavailable  
LAN \= available

Core functionality includes:

* opening ShareBox;  
* authentication;  
* browsing;  
* uploads;  
* downloads;  
* local UI assets.

The product MUST NOT secretly depend on cloud infrastructure for ordinary transfers.

---

# **38\. Addressing and Discovery**

ShareBox SHOULD provide multiple connection mechanisms.

Primary:

### **QR Code**

Best first-time experience.

Secondary:

### **Friendly Local Hostname**

Example:

sharebox.local

This SHOULD be implemented using local discovery such as mDNS where platform/network support allows.

Fallback:

### **Local IP Address**

Example:

192.168.1.24:8765

The user should not normally need to type this manually, but it provides an important fallback when local hostname discovery fails.

---

# **39\. Network Changes**

ShareBox MUST tolerate common network changes.

Examples:

* Wi-Fi disconnect/reconnect;  
* host switching Wi-Fi networks;  
* DHCP assigning a different IP;  
* computer waking from sleep;  
* hotspot being enabled/disabled.

The desktop application should refresh connection information and QR data where required.

A changed host IP MUST NOT invalidate the identity of trusted devices.

---

# **40\. Security Model**

ShareBox should assume that a local network is **not inherently trusted**.

Potential attackers may include another device connected to the same Wi-Fi.

Therefore, knowledge of:

192.168.x.x:PORT

MUST NOT be sufficient to browse files.

Authorization is required.

---

# **41\. Filesystem Security Boundary**

The configured ShareBox directory is the maximum filesystem boundary exposed to clients.

A client request MUST NEVER be capable of escaping this directory.

The implementation MUST defend against:

* `../` traversal;  
* encoded traversal;  
* symlink-related escape where applicable;  
* malformed paths;  
* absolute-path injection;  
* filesystem separator tricks;  
* null-byte/path parsing attacks.

Every resolved file path MUST be verified to remain within the configured ShareBox root before access.

This is a critical security requirement.

---

# **42\. Upload Security**

Uploaded filenames MUST be sanitized for the host operating system.

Client-supplied paths MUST NOT determine arbitrary filesystem destinations.

Uploads MUST be restricted to the authenticated device's upload directory.

ShareBox MUST handle filenames that contain:

* reserved characters;  
* Unicode;  
* very long names;  
* duplicate names;  
* platform-invalid names.

---

# **43\. Web Security**

The implementation must consider, where applicable:

* authentication token protection;  
* CSRF;  
* XSS through malicious filenames;  
* content disposition;  
* unsafe inline file rendering;  
* session fixation;  
* brute-force pairing attempts;  
* unauthorized API access.

All file names and user-controlled values rendered into HTML MUST be treated as untrusted input.

---

# **44\. Privacy Principles**

ShareBox MUST NOT require:

* registration;  
* email;  
* phone number;  
* social login;  
* cloud account.

Core file contents MUST NOT be uploaded to ShareBox-operated infrastructure.

Telemetry SHOULD be absent by default in V1.

If telemetry is introduced later, it must be:

* transparent;  
* privacy-preserving;  
* optional where appropriate;  
* incapable of transmitting user file contents.

---

# **45\. Recommended Technical Stack**

For V1, the recommended architecture is:

### **Backend**

**Python \+ FastAPI**

Responsibilities:

* API;  
* authentication;  
* pairing;  
* filesystem access;  
* uploads;  
* downloads;  
* static web application serving;  
* network/service state.

### **Web Client**

Prefer a lightweight frontend.

The frontend SHOULD avoid unnecessary framework complexity.

A modern lightweight JavaScript/TypeScript architecture may be used if it materially improves maintainability.

The frontend MUST compile/package entirely with ShareBox and operate offline.

### **Desktop Application**

Use a cross-platform-capable desktop UI approach that integrates cleanly with Python and provides:

* window management;  
* tray support;  
* native dialogs;  
* folder picker;  
* notifications;  
* OS integration.

The final framework should be selected based on packaging reliability, maintainability and cross-platform support rather than visual novelty.

---

# **46\. Backend Process Model**

The desktop application and local server should behave as one coherent product.

Implementation may use:

Desktop Process  
      │  
      └── Backend Server

or controlled subprocesses if technically preferable.

Regardless of implementation, the application MUST:

* start the backend reliably;  
* know whether it started successfully;  
* stop it cleanly;  
* avoid orphaned processes;  
* recover from failures;  
* expose meaningful service state to the UI.

---

# **47\. Local Configuration**

ShareBox requires persistent configuration independent of the shared folder.

Configuration may include:

* selected ShareBox folder;  
* preferred port;  
* startup preference;  
* trusted-device records;  
* device names;  
* authentication material;  
* UI preferences;  
* version/migration information.

Configuration MUST use the appropriate application-data location for each operating system.

Secrets MUST NOT be stored casually in plaintext where a safer OS-supported mechanism is practical.

---

# **48\. API Architecture**

The web client SHOULD communicate with the backend through a versioned internal API.

Conceptually:

/api/v1/...

The API should cover:

* authentication;  
* pairing;  
* files;  
* folders;  
* uploads;  
* downloads;  
* device/session information;  
* server state where appropriate.

Exact endpoint definitions will be specified in the technical implementation section.

The API MUST enforce authorization server-side.

Hiding controls in the UI is not security.

---

# **49\. Large-File Handling**

ShareBox MUST be designed for files substantially larger than typical screenshots/documents.

The implementation MUST avoid architectures where a 5 GB transfer requires approximately 5 GB of application RAM.

Uploads and downloads SHOULD use streaming/chunked I/O.

The transfer implementation should primarily be constrained by:

* storage speed;  
* LAN throughput;  
* device/browser limitations;

rather than unnecessary application buffering.

---

# **50\. Concurrent Access**

Multiple trusted devices MAY connect simultaneously.

Example:

                ShareBox PC  
                /     |      \\  
               /      |       \\  
          iPhone   Android    iPad

One device downloading a large file MUST NOT unnecessarily block another device from browsing or initiating another transfer.

The backend architecture should use appropriate asynchronous/concurrent I/O.

---

# **51\. Transfer Failure Behaviour**

Failures must be explicit.

Examples:

* network disconnected;  
* host sleeping;  
* storage full;  
* source file removed;  
* permission denied;  
* upload interrupted.

The interface MUST NOT display a transfer as successful until the server confirms successful completion.

Partially uploaded files SHOULD NOT appear indistinguishably from complete files.

Implementation SHOULD use temporary/incomplete file handling and finalize atomically where practical.

---

# **52\. Desktop vs Web Responsibilities**

This separation is intentional.

### **Desktop Application**

Controls **ShareBox itself**:

* server;  
* network;  
* pairing;  
* devices;  
* settings;  
* folder selection.

### **Web Application**

Controls **interaction with shared content**:

* browsing;  
* searching;  
* previews;  
* downloads;  
* uploads.

### **Operating-System File Manager**

Controls **host-side file management**:

* moving;  
* renaming;  
* deleting;  
* organizing files.

The Design AI and Code AI MUST preserve this separation.

---

# **53\. Cross-Platform Strategy**

ShareBox must be architected so core business logic is platform-independent.

Shared components should include:

* backend;  
* web client;  
* authentication;  
* file-transfer logic;  
* device management;  
* configuration abstractions.

Platform-specific code should be isolated behind defined interfaces.

Examples include:

platform/  
├── windows/  
├── macos/  
└── linux/

where appropriate.

---

# **54\. Release Strategy**

Development order:

Cross-platform architecture  
          ↓  
Windows implementation  
          ↓  
Windows V1 stabilization  
          ↓  
macOS packaging/integration  
          ↓  
Linux packaging/integration

Windows-specific shortcuts MUST NOT be embedded deeply into core logic where they would make later ports unnecessarily expensive.

---

# **55\. Open-Source Requirements**

ShareBox is intended to be open source.

The repository SHOULD therefore be structured for external contribution.

It MUST include, before public release:

* clear README;  
* installation/build instructions;  
* development setup;  
* architecture overview;  
* contribution guidelines;  
* license;  
* issue templates where useful;  
* security reporting process.

Dependencies MUST use licenses compatible with the selected ShareBox open-source license.

No proprietary dependency should become essential to core ShareBox functionality without explicit project approval.

---

# **56\. Repository Principles**

The codebase should have clear boundaries between:

sharebox/  
├── backend/  
├── desktop/  
├── web/  
├── platform/  
├── tests/  
├── docs/  
└── build/

The exact structure may evolve, but separation of concerns MUST remain clear.

Code AI must not collapse unrelated functionality into large monolithic files merely because doing so is faster to generate.

---

# **57\. Design Direction**

ShareBox should visually communicate:

* simplicity;  
* speed;  
* proximity;  
* privacy;  
* reliability.

It should feel like a polished operating-system utility rather than:

* an enterprise dashboard;  
* a cloud storage SaaS;  
* an admin panel;  
* a developer server interface.

The UI should use restrained visual hierarchy and generous clarity.

Technical information should only appear where it helps the user solve a problem.

---

# **58\. Desktop Screen Inventory**

Design AI MUST account for at least:

1. First launch/onboarding  
2. Main control center — running  
3. Main control center — stopped  
4. Pair new device  
5. Pairing success  
6. Trusted devices  
7. Device details/revoke confirmation  
8. Settings  
9. Shared-folder selection/change  
10. No-network state  
11. Server/error state  
12. System tray menu  
13. Relevant confirmation dialogs  
14. Relevant notifications

Not every item needs to be a separate full screen. Modals, panels and inline states should be used appropriately.

---

# **59\. Web Screen Inventory**

Design AI MUST account for:

1. Unpaired/unauthorized state  
2. Pairing state  
3. File browser  
4. Folder view  
5. Search state  
6. Empty folder  
7. File preview  
8. Upload selection  
9. Upload in progress  
10. Upload success  
11. Upload failure  
12. Download interaction  
13. Connection lost  
14. Host unavailable  
15. Authorization revoked/expired  
16. General error state

The web experience MUST be designed mobile-first.

---

# **60\. Accessibility**

ShareBox SHOULD meet reasonable modern accessibility expectations.

The interfaces should support:

* keyboard navigation;  
* visible focus states;  
* sufficient contrast;  
* semantic controls;  
* screen-reader labels;  
* touch targets suitable for mobile;  
* status information that does not rely solely on color.

Animations must not be necessary to understand application state.

---

# **61\. Performance Expectations**

ShareBox should remain lightweight when idle.

The application SHOULD avoid:

* high idle CPU usage;  
* unnecessary polling;  
* excessive memory usage;  
* constant filesystem rescanning;  
* unnecessary background network traffic.

The product may use filesystem events/watchers where appropriate to keep the browser state current efficiently.

---

# **62\. Reliability Principle**

ShareBox is infrastructure-like software.

Reliability is more important than animation, visual novelty or excessive features.

A boring transfer that works every time is preferable to an impressive interface surrounding unreliable networking.

Code AI MUST prioritize:

1. correctness;  
2. security;  
3. transfer reliability;  
4. recoverability;  
5. performance;  
6. UX polish;  
7. optional features.

---

# **63\. V1 Scope Lock**

The V1 product is:

> **A secure, local-first shared folder hosted by a desktop computer and accessible through browsers on trusted devices, supporting bidirectional file transfer without requiring internet connectivity or client applications.**

V1 includes:

* desktop host application;  
* normal ShareBox filesystem folder;  
* local server;  
* browser client;  
* file browsing;  
* subfolders;  
* search;  
* downloads;  
* uploads;  
* per-device upload folders;  
* multi-file upload;  
* appropriate previews;  
* QR pairing;  
* remembered trusted devices;  
* automatic trusted-device reconnection;  
* device revocation;  
* QR/local hostname/IP connection options;  
* system tray;  
* launch at startup;  
* offline operation;  
* Windows packaging.

Anything beyond this requires explicit scope approval.

---

# **64\. Future Architecture Considerations**

V1 should not implement future features prematurely, but architecture SHOULD avoid making the following unnecessarily difficult.

### **Clipboard**

Potential future structure:

ShareBox  
├── Files  
└── Clipboard

or another UX model determined later.

Clipboard functionality may eventually support:

* copied text;  
* copied images;  
* URLs;  
* clipboard history;  
* cross-device clipboard delivery.

The existing per-device identity model is intentionally useful for attributing future device-originated clipboard content.

### **Additional possibilities**

Future versions may investigate:

* text/link sharing;  
* PWA installation;  
* transfer history;  
* temporary sharing;  
* device-specific permissions;  
* native mobile applications if browser limitations justify them;  
* direct device-to-device transfer;  
* optional encrypted remote access.

These are **not V1 requirements**.

---

# **65\. Instructions to Design AI**

The Design AI must treat this specification as product requirements rather than inspiration.

It MUST:

* design every required state;  
* preserve the desktop/web responsibility separation;  
* prioritize mobile browser usability;  
* keep the desktop application compact;  
* avoid unnecessary dashboard patterns;  
* make pairing understandable to nontechnical users;  
* make transfer status obvious;  
* make security understandable without exposing implementation jargon;  
* design responsive layouts;  
* account for long filenames;  
* account for empty/loading/error states;  
* account for multiple simultaneous uploads;  
* provide reusable components and a consistent design system.

It MUST NOT independently introduce major product features such as:

* accounts;  
* cloud storage;  
* chat;  
* browser deletion;  
* browser file management;  
* social functionality.

Any such proposal belongs outside the primary V1 design.

---

# **66\. Instructions to Code AI**

Code AI must treat this document as the authoritative product specification.

It MUST:

* preserve security boundaries;  
* keep platform-specific code isolated;  
* use maintainable modules;  
* implement server-side authorization;  
* stream large files;  
* sanitize untrusted input;  
* validate filesystem paths;  
* handle errors explicitly;  
* write automated tests for critical behaviour;  
* document important architectural decisions;  
* avoid unnecessary dependencies;  
* avoid external runtime services for core functionality;  
* preserve offline operation.

Code AI MUST NOT make silent product decisions where a change materially contradicts this specification.

If a requirement cannot reasonably be implemented as specified, the AI should identify:

1. the requirement;  
2. the technical conflict;  
3. its recommended alternative;  
4. the consequences of that alternative;

before changing the architecture.

---

# **67\. Definition of Product Success**

ShareBox succeeds when this interaction becomes ordinary:

Take screenshot on PC  
        ↓  
Save to ShareBox  
        ↓  
Pick up iPhone  
        ↓  
Open ShareBox  
        ↓  
Tap screenshot  
        ↓  
Done

and the reverse:

Take photo on phone  
        ↓  
Open ShareBox  
        ↓  
Upload  
        ↓  
Open ShareBox folder on PC  
        ↓  
Photo is there

without:

* WhatsApp;  
* email;  
* cloud storage;  
* USB;  
* Bluetooth pairing;  
* mobile data;  
* internet dependency;  
* installing an app on the phone.

That simplicity is the core product requirement.

### **Part II — Engineering & System Architecture**

---

# **68\. Engineering Architecture Overview**

ShareBox uses a **host-client architecture**.

The desktop computer is the host. It owns the filesystem, runs the ShareBox backend and serves the browser client.

┌───────────────────────────────────────────────────────┐  
│                    HOST COMPUTER                      │  
│                                                       │  
│  ┌──────────────────┐      ┌───────────────────────┐ │  
│  │ Desktop App      │◄────►│ ShareBox Backend      │ │  
│  │                  │      │                       │ │  
│  │ • Status         │      │ • API                 │ │  
│  │ • Pairing        │      │ • Authentication      │ │  
│  │ • Devices        │      │ • File Operations     │ │  
│  │ • Settings       │      │ • Transfer Engine     │ │  
│  └──────────────────┘      │ • Web Client Server   │ │  
│                            └───────────┬───────────┘ │  
│                                        │             │  
│                              ┌─────────▼──────────┐  │  
│                              │ ShareBox Folder    │  │  
│                              │                   │  │  
│                              │ Files / Folders   │  │  
│                              │ Device Uploads    │  │  
│                              └────────────────────┘  │  
└───────────────────────────┬───────────────────────────┘  
                            │  
                      Local Network  
                            │  
              ┌─────────────┼─────────────┐  
              ▼             ▼             ▼  
           iPhone        Android        Laptop  
           Browser       Browser        Browser

The architecture MUST maintain separation between:

1. desktop presentation;  
2. backend/application logic;  
3. web presentation;  
4. filesystem;  
5. platform-specific integration.

---

# **69\. Recommended Technology Stack**

## **69.1 Backend**

**Python 3 \+ FastAPI**

FastAPI handles:

* HTTP API;  
* browser authentication;  
* pairing;  
* directory listing;  
* uploads;  
* downloads;  
* static frontend delivery;  
* transfer state where required.

The backend SHOULD use asynchronous I/O where it improves network concurrency.

---

## **69.2 Web Client**

Recommended:

**TypeScript \+ lightweight frontend architecture**

A full heavyweight SPA framework is not mandatory.

The implementation may use a lightweight framework if it materially improves:

* component organization;  
* state management;  
* maintainability;  
* testing.

The compiled web application MUST be bundled with ShareBox.

There MUST be no essential runtime dependency on:

* npm servers;  
* CDNs;  
* Google Fonts;  
* externally hosted JavaScript;  
* externally hosted icons;  
* internet APIs.

---

# **70\. Desktop Framework**

The desktop UI framework MUST support:

* Windows;  
* macOS;  
* Linux;  
* system tray/menu bar;  
* native folder selection;  
* notifications;  
* background operation;  
* packaging into standalone applications.

The framework SHOULD integrate naturally with the Python backend.

The final framework may be selected during the implementation proof-of-concept after verifying:

* packaging reliability;  
* tray support;  
* startup behaviour;  
* native dialog support;  
* application size;  
* cross-platform maturity.

**Code AI MUST NOT choose Electron by default merely because it is familiar.**

A heavyweight Chromium runtime is difficult to justify for ShareBox's small control interface unless it provides a demonstrated implementation advantage.

---

# **71\. Core Module Architecture**

Recommended logical backend structure:

sharebox/  
│  
├── backend/  
│   ├── app/  
│   │   ├── api/  
│   │   ├── auth/  
│   │   ├── pairing/  
│   │   ├── devices/  
│   │   ├── files/  
│   │   ├── transfers/  
│   │   ├── network/  
│   │   ├── discovery/  
│   │   ├── config/  
│   │   ├── security/  
│   │   └── services/  
│   │  
│   └── tests/  
│  
├── desktop/  
│   ├── ui/  
│   ├── tray/  
│   ├── settings/  
│   └── platform/  
│  
├── web/  
│   ├── src/  
│   ├── components/  
│   ├── views/  
│   ├── services/  
│   └── assets/  
│  
├── platform/  
│   ├── windows/  
│   ├── macos/  
│   └── linux/  
│  
├── build/  
├── docs/  
└── tests/

This is a structural recommendation rather than a mandatory literal directory tree.

Code organization MUST nevertheless preserve these boundaries.

---

# **72\. Application Lifecycle**

ShareBox has five principal lifecycle stages:

NOT RUNNING  
     ↓  
INITIALIZING  
     ↓  
READY  
     ↓  
SHARING  
     ↓  
SHUTTING DOWN

Failure states may interrupt initialization or sharing.

---

# **73\. Startup Sequence**

When ShareBox starts:

1. Load application configuration.  
2. Validate configuration schema/version.  
3. Resolve configured ShareBox folder.  
4. Initialize persistent local state.  
5. Load trusted devices.  
6. Detect available network interfaces.  
7. Select usable LAN interface(s).  
8. Determine service port.  
9. Initialize backend.  
10. Start local HTTP service.  
11. Start local discovery service where available.  
12. Determine reachable local addresses.  
13. Initialize desktop UI/tray.  
14. Report ShareBox status.

Failures MUST NOT leave orphaned backend processes.

---

# **74\. Shutdown Sequence**

When the user explicitly quits ShareBox:

1. Stop accepting new transfers.  
2. Handle active transfers according to shutdown policy.  
3. Stop discovery advertisement.  
4. Close server listeners.  
5. Flush necessary state.  
6. Close database/config resources.  
7. terminate background workers;  
8. remove temporary resources where safe;  
9. exit cleanly.

Closing the desktop window MUST NOT trigger this sequence unless the user explicitly chooses Quit.

---

# **75\. Local Persistent State**

ShareBox needs a small local state store for information that does not belong in the shared folder.

Recommended:

**SQLite** for structured application state.

SQLite is appropriate because ShareBox requires:

* no external database server;  
* minimal installation;  
* transactional updates;  
* cross-platform support;  
* simple backup/migration;  
* structured trusted-device records.

---

# **76\. Database Responsibilities**

The database MAY store:

### **Trusted devices**

* internal ID;  
* display name;  
* authentication information;  
* created timestamp;  
* last-seen timestamp;  
* revoked status where needed.

### **Application metadata**

* schema version;  
* migrations;  
* local installation identifier.

### **Security metadata**

* token hashes/identifiers;  
* pairing state where persistence is necessary.

The database MUST NOT store:

* copies of shared files;  
* file contents;  
* a canonical mirror of the ShareBox directory.

The filesystem remains authoritative for files.

---

# **77\. Configuration Responsibilities**

Simple application preferences SHOULD remain configuration rather than relational data where appropriate.

Example conceptual configuration:

{  
  "shared\_folder": "...",  
  "port": 8765,  
  "launch\_at\_startup": true,  
  "start\_sharing\_automatically": true  
}

Configuration and database formats MUST be versioned so future releases can migrate them safely.

---

# **78\. Host Installation Identity**

Every ShareBox installation MUST generate a cryptographically random unique host identifier on first successful initialization.

Conceptually:

host\_id \= random UUID

The host identity:

* persists across restarts;  
* does not depend on IP address;  
* does not depend on hostname;  
* does not change when Wi-Fi changes.

It MAY be used internally during pairing and discovery.

---

# **79\. Device Identity**

Every paired client receives a random internal device identifier.

Example:

device\_id:  
9f4d10d7-...

Human-readable names are separate:

display\_name:  
"Bolu's iPhone"

Security MUST depend on the internal identity and credentials, not the display name.

---

# **80\. Authentication Architecture**

ShareBox uses **trusted-device authentication**.

There are two distinct states:

### **Untrusted**

The browser has not successfully paired with this ShareBox host.

It cannot browse files.

### **Trusted**

The browser possesses valid authorization credentials previously issued by this host.

It may access permitted ShareBox functionality.

---

# **81\. Authentication Credential Requirements**

A successful pairing MUST generate a high-entropy authorization credential.

The credential MUST:

* be cryptographically random;  
* be infeasible to guess;  
* belong to a specific trusted device;  
* be revocable;  
* persist across normal browser sessions;  
* not derive from IP address.

The server SHOULD store a secure verifier/hash rather than a directly reusable plaintext credential wherever the authentication design permits.

---

# **82\. Browser Credential Storage**

The trusted-device credential SHOULD be stored using a browser mechanism appropriate to the final authentication protocol.

Security-sensitive credentials SHOULD prefer protected cookie-based storage where feasible rather than exposing long-lived tokens directly to ordinary frontend JavaScript.

The implementation MUST consider:

* XSS;  
* token theft;  
* persistence;  
* browser storage clearing;  
* SameSite behaviour;  
* local-network hostname/IP changes.

The exact storage mechanism MUST be tested on Safari iOS and Chromium browsers before architecture lock.

---

# **83\. Pairing Principle**

A QR code is an **initial authorization mechanism**, not permanent authentication.

The QR payload SHOULD contain a short-lived pairing capability.

Conceptually:

sharebox://pair?  
host=...  
pairing\_token=...

or an HTTP/HTTPS equivalent appropriate to browser-based pairing.

The exact final URI format will depend on the transport/security implementation.

---

# **84\. Pairing Session**

When the host selects **Pair Device**:

1. Backend generates a cryptographically random pairing token.  
2. Token receives a short expiry.  
3. Desktop application displays a QR code containing the pairing URL/capability.  
4. Client scans QR.  
5. Browser reaches ShareBox.  
6. Backend validates pairing token.  
7. Client establishes its trusted-device identity.  
8. Long-lived device credential is issued.  
9. Pairing token becomes unusable.  
10. Device is added to Trusted Devices.  
11. Pairing UI reports success.

Pairing tokens MUST be single-use.

---

# **85\. Pairing Expiration**

Pairing sessions SHOULD expire quickly.

Recommended target:

**approximately 2–5 minutes.**

The exact value may be determined during UX testing.

Expired QR codes MUST NOT pair new devices.

The desktop application must allow generation of a fresh pairing session.

---

# **86\. Pairing Replay Protection**

After successful use:

pairing\_token → consumed

The same token MUST NOT authorize another device.

The server must atomically mark the token as consumed.

---

# **87\. Pairing Concurrency**

V1 MAY allow one active pairing session at a time.

Starting a new pairing session MAY invalidate the previous unused session.

This simplifies the trust model and is sufficient for personal use.

---

# **88\. Trusted Device Record**

Conceptual schema:

TrustedDevice  
────────────────────────────  
id  
display\_name  
credential\_verifier  
created\_at  
last\_seen\_at  
revoked\_at  
upload\_folder\_name

Additional security metadata MAY be added.

The schema MUST NOT use the device name as a primary key.

---

# **89\. Device Revocation Flow**

When the host selects:

> Revoke Device

the UI SHOULD require confirmation.

After confirmation:

1. device is marked revoked or removed;  
2. active credentials are invalidated;  
3. existing sessions are rejected;  
4. subsequent API calls return unauthorized;  
5. browser is redirected to an authorization-required state.

Existing uploaded files remain untouched.

---

# **90\. Revocation Immediacy**

Revocation SHOULD take effect immediately.

A currently connected revoked device must not retain access until the next application restart.

Every protected request MUST ultimately be validated against current server-side authorization state.

---

# **91\. Authentication Failure Behaviour**

Protected API requests from an unauthorized device SHOULD return:

401 Unauthorized

or:

403 Forbidden

depending on whether authentication is missing/invalid or the authenticated identity lacks permission.

The web client should convert this into a human-readable state rather than exposing raw HTTP errors.

---

# **92\. Transport Security Challenge**

Local browser-based applications create an important constraint:

**HTTPS is desirable, but trusted public TLS certificates generally cannot simply be issued for arbitrary private LAN addresses such as `192.168.x.x`.**

Self-signed certificates create browser warnings and poor onboarding.

Therefore, V1 MUST NOT pretend this problem does not exist.

---

# **93\. V1 Transport Strategy**

Initial implementation MAY use HTTP on the local LAN while protecting access using:

* high-entropy credentials;  
* short-lived pairing tokens;  
* server-side authorization;  
* strict filesystem boundaries;  
* secure application design.

However, HTTP does not protect traffic from a capable attacker who can observe/interfere with LAN traffic.

This limitation MUST be documented.

The engineering prototype SHOULD investigate practical local HTTPS approaches before final release architecture is frozen.

ShareBox MUST NOT instruct users to bypass browser certificate warnings as its normal UX.

---

# **94\. Security Scope of V1**

ShareBox V1 aims to prevent:

* casual unauthorized access;  
* URL guessing;  
* unauthorized browsing;  
* stale/revoked-device access;  
* path traversal;  
* arbitrary filesystem access;  
* unsafe uploads.

V1 MUST NOT claim that plain HTTP provides confidentiality against hostile LAN traffic.

Security documentation must accurately represent the actual transport.

---

# **95\. Network Binding**

The backend MUST NOT blindly expose itself on every network interface without evaluating available interfaces.

ShareBox should identify usable local interfaces and expose reachable LAN addresses.

It SHOULD avoid inappropriate interfaces where practical, including:

* loopback-only;  
* disconnected interfaces;  
* irrelevant virtual adapters.

Multiple legitimate LAN interfaces may exist simultaneously.

---

# **96\. Loopback Access**

The server SHOULD remain reachable locally through:

127.0.0.1

or:

localhost

where appropriate.

This enables host-side testing and potentially the host web interface.

---

# **97\. Port Strategy**

ShareBox SHOULD have a default application port.

Example:

8765

The exact port is not a product requirement.

If unavailable, ShareBox SHOULD:

1. detect the conflict;  
2. select an appropriate available fallback where safe;  
3. update discovery/QR information;  
4. expose the actual port in diagnostic information.

A port conflict should not ordinarily make the application unusable.

---

# **98\. Local Discovery**

ShareBox SHOULD advertise itself using mDNS where supported.

Conceptually:

sharebox.local

However, `.local` hostname behaviour differs across operating systems and network environments.

Therefore, mDNS MUST be treated as a convenience layer rather than the only connection mechanism.

---

# **99\. Discovery Fallback Hierarchy**

Connection methods should be prioritized approximately as:

QR pairing  
    ↓  
Friendly local hostname  
    ↓  
LAN IP \+ port

If mDNS fails, QR codes can contain the currently reachable LAN address.

The application must remain usable without mDNS.

---

# **100\. QR Payload Selection**

When generating a pairing QR, ShareBox should select a host address reachable by the client.

If the host has multiple candidate interfaces:

Ethernet  
Wi-Fi  
VPN  
Virtual Adapter

the system SHOULD rank likely LAN interfaces.

If ambiguity cannot be resolved reliably, the desktop UI MAY allow the user to select the network used for ShareBox.

---

# **101\. Network Interface Changes**

The network module MUST detect or periodically verify relevant interface changes.

When the host address changes:

* backend remains operational where possible;  
* discovery advertisement updates;  
* desktop connection information updates;  
* newly generated QR codes use the current address.

Trusted-device identity remains unchanged.

---

# **102\. Client Bookmark Problem**

A raw IP bookmark can become stale when DHCP changes the host IP.

Therefore, ShareBox SHOULD encourage a stable local hostname where supported.

The browser UI MAY also provide an **Add to Home Screen / bookmark** hint where appropriate, but this must not become mandatory.

---

# **103\. Host Sleep**

When the host computer sleeps, ShareBox becomes unavailable.

The client SHOULD show a clear state such as:

> ShareBox can't reach the host computer.

It MUST NOT imply that files have been deleted or authentication has failed.

When the host wakes and becomes reachable, the browser SHOULD recover gracefully.

---

# **104\. Filesystem Service Architecture**

All file operations MUST pass through a centralized filesystem service.

API handlers MUST NOT independently construct arbitrary filesystem paths.

Conceptually:

API  
 ↓  
FileService  
 ↓  
PathSecurity  
 ↓  
Filesystem

This ensures path validation is implemented consistently.

---

# **105\. Root Boundary Validation**

Every requested path must be:

1. normalized;  
2. resolved;  
3. checked against the canonical ShareBox root;  
4. rejected if it escapes that root.

Conceptually:

requested path  
      ↓  
resolve canonical path  
      ↓  
is descendant of ShareBox root?  
      ↓  
 YES              NO  
  │                │  
allow             reject

String-prefix checks alone MUST NOT be considered sufficient.

---

# **106\. Symlink Handling**

Symbolic links can potentially escape the ShareBox root.

V1 SHOULD use a conservative policy.

A symlink resolving outside the configured ShareBox root MUST NOT expose the external target.

The implementation MAY reject symlinks entirely from browser access if this provides the safest predictable cross-platform behaviour.

The chosen policy must be explicitly tested.

---

# **107\. Directory Listing API**

Conceptual endpoint:

GET /api/v1/files

Optional query:

?path=Projects/Glide

Conceptual response:

{  
  "path": "Projects/Glide",  
  "items": \[  
    {  
      "name": "PRD.pdf",  
      "type": "file",  
      "size": 438102,  
      "modified\_at": "2026-08-07T08:40:00Z"  
    },  
    {  
      "name": "Assets",  
      "type": "directory",  
      "modified\_at": "2026-08-07T08:30:00Z"  
    }  
  \]  
}

The server MUST NOT return unnecessary absolute host filesystem paths.

---

# **108\. Download API**

Conceptual endpoint:

GET /api/v1/files/download?path=...

The endpoint MUST:

* authenticate client;  
* validate path;  
* ensure target is a permitted regular file;  
* stream file;  
* provide safe content headers;  
* handle file disappearance gracefully.

---

# **109\. Upload API**

Conceptual endpoint:

POST /api/v1/uploads

The server determines the destination from authenticated device identity.

The client MUST NOT be allowed to submit:

destination=C:\\Users\\...

or another arbitrary host path.

Conceptually:

authenticated device  
       ↓  
device ID  
       ↓  
device upload directory  
       ↓  
safe generated destination

---

# **110\. Upload Folder Resolution**

Suppose:

Device ID:  
abc123

Display name:  
Bolu's iPhone

ShareBox maintains a stable safe folder mapping.

Example:

upload\_folder\_name:  
Bolu's iPhone

If another trusted device uses the same display name, ShareBox MUST generate a unique filesystem-safe alternative.

Example:

Bolu's iPhone  
Bolu's iPhone (2)

Changing the display name later SHOULD NOT silently move or rename existing filesystem content.

Folder renaming should be a deliberate future operation if supported.

---

# **111\. Lazy Upload Folder Creation**

The device upload directory is created only when:

1. authenticated device begins a valid upload;  
2. destination has been resolved;  
3. server is ready to write.

Pairing alone MUST NOT create it.

---

# **112\. Upload Temporary Files**

Uploads SHOULD initially write to a temporary/incomplete destination.

Conceptually:

IMG\_1001.jpeg.sharebox-part

After successful completion:

validate completion  
      ↓  
atomic rename where supported  
      ↓  
IMG\_1001.jpeg

Failed/incomplete transfers should not masquerade as completed user files.

Temporary files SHOULD be cleaned up safely.

---

# **113\. Upload Collision Algorithm**

Given:

photo.jpg

if it already exists:

photo (1).jpg

then:

photo (2).jpg

etc.

The collision algorithm MUST be race-safe enough that simultaneous uploads cannot accidentally overwrite one another.

---

# **114\. Upload Size**

ShareBox SHOULD NOT impose an unnecessarily small application-level file-size limit.

If a safety limit is implemented, it must be configurable or large enough for normal large-file transfers.

Available disk space and platform/browser constraints are more relevant than arbitrary SaaS-style upload limits.

---

# **115\. Disk Space Handling**

Before and during upload, ShareBox SHOULD detect storage failures.

If the host drive becomes full:

* transfer fails cleanly;  
* client receives an understandable error;  
* incomplete temporary file is handled safely;  
* existing files remain intact.

---

# **116\. File Metadata**

V1 file metadata should remain minimal.

Required where available:

* name;  
* item type;  
* size for files;  
* modification timestamp.

Optional:

* MIME/content type;  
* thumbnail availability.

ShareBox MUST NOT build an unnecessarily complex metadata database.

---

# **117\. MIME Detection**

MIME detection MAY use:

* filename extension;  
* standard library/platform facilities;  
* safe lightweight detection libraries.

MIME type MUST NOT be trusted as proof that file contents are safe.

Preview behaviour should remain conservative.

---

# **118\. Preview Architecture**

The web client may request files for preview through authenticated endpoints.

Preview support SHOULD prioritize browser-native capabilities.

ShareBox SHOULD NOT transcode arbitrary media in V1.

For example:

JPEG → browser image viewer  
MP4  → browser video element if supported  
PDF  → browser-native/embed strategy  
ZIP  → download only

Unsupported files remain downloadable.

---

# **119\. Search Architecture**

V1 search SHOULD remain filesystem-based.

Conceptually:

GET /api/v1/search?q=screenshot

The server searches filenames within ShareBox.

Search MUST respect the root boundary.

Search SHOULD be case-insensitive where platform behaviour allows a predictable implementation.

A persistent full-text index is unnecessary for V1.

---

# **120\. Search Safety**

Search MUST NOT:

* inspect arbitrary directories outside ShareBox;  
* execute files;  
* parse document contents;  
* follow unsafe external symlinks.

V1 searches filenames/folder names only.

---

# **121\. Filesystem Change Detection**

ShareBox SHOULD detect host-side filesystem changes efficiently.

Preferred strategy:

* OS filesystem watcher where reliable;  
* controlled refresh/fallback where required.

Examples:

Host adds screenshot  
       ↓  
watcher detects change  
       ↓  
browser state becomes stale  
       ↓  
refresh/update

The browser MAY use polling initially, but the architecture SHOULD permit more efficient real-time updates.

---

# **122\. Real-Time Browser Updates**

V1 SHOULD support automatic file-list updates where practical.

Potential mechanisms include:

* Server-Sent Events;  
* WebSocket;  
* lightweight polling.

For ShareBox's predominantly server-to-client filesystem notifications, **Server-Sent Events should be evaluated before introducing WebSocket complexity**.

The implementation should choose the simplest reliable mechanism.

---

# **123\. Transfer Progress**

Upload progress SHOULD be measured client-side using bytes transmitted where supported.

Download progress may depend on browser capabilities and whether downloads are delegated to the browser.

ShareBox MUST NOT fabricate precise progress values when they cannot be known.

---

# **124\. Transfer Cancellation**

V1 SHOULD allow active uploads initiated through the ShareBox UI to be cancelled where technically reliable.

Browser-managed downloads MAY use normal browser cancellation behaviour.

Cancellation must leave no completed-looking corrupt file.

---

# **125\. Concurrent Transfers**

The backend MUST support multiple independent transfer streams.

Concurrency limits MAY be introduced to protect host resources.

Any limit SHOULD be sensible for personal LAN usage rather than artificially restrictive.

---

# **126\. API Error Format**

API errors SHOULD use a consistent structure.

Conceptually:

{  
  "error": {  
    "code": "FILE\_NOT\_FOUND",  
    "message": "The requested file no longer exists."  
  }  
}

Machine-readable codes allow the web client to present appropriate UX.

---

# **127\. Core Error Codes**

The implementation should define stable codes for at least:

UNAUTHORIZED  
DEVICE\_REVOKED  
PAIRING\_INVALID  
PAIRING\_EXPIRED  
PAIRING\_CONSUMED

FILE\_NOT\_FOUND  
FOLDER\_NOT\_FOUND  
INVALID\_PATH  
ACCESS\_DENIED

UPLOAD\_FAILED  
DISK\_FULL  
FILE\_COLLISION\_FAILURE

NETWORK\_UNAVAILABLE  
SERVER\_ERROR

Internal stack traces MUST NOT be sent to normal clients.

---

# **128\. Logging**

ShareBox MUST maintain useful local diagnostic logs.

Logs SHOULD include:

* application startup/shutdown;  
* server failures;  
* network changes;  
* pairing events;  
* authentication failures;  
* transfer failures;  
* filesystem errors;  
* unexpected exceptions.

Logs MUST NOT contain:

* file contents;  
* raw authentication secrets;  
* pairing secrets;  
* unnecessarily sensitive information.

Filename logging should be minimized or configurable if privacy considerations warrant it.

---

# **129\. Debug Mode**

Developer builds MAY expose additional diagnostic information.

Production builds MUST NOT expose debug stack traces or development server interfaces to LAN clients.

---

# **130\. Desktop-to-Backend Communication**

The desktop UI needs access to privileged host operations unavailable to browser clients.

Examples:

* change shared folder;  
* revoke device;  
* stop server;  
* change startup settings.

These operations MUST NOT automatically be exposed through the normal LAN client API.

If implemented over HTTP internally, privileged control endpoints MUST be restricted to trusted local desktop communication.

A remote trusted phone MUST NOT gain host-administration rights merely because it can access ShareBox files.

---

# **131\. Privilege Separation**

There are therefore at least two logical permission classes:

HOST ADMIN  
────────────  
Configure ShareBox  
Manage devices  
Change folder  
Start/stop service  
Settings

TRUSTED CLIENT  
──────────────  
Browse  
Search  
Preview  
Download  
Upload

The API architecture MUST preserve this distinction.

---

# **132\. Desktop Main State Model**

The desktop UI should receive structured state from backend services.

Conceptually:

ShareBoxState  
────────────────────────  
service\_status  
network\_status  
shared\_folder  
reachable\_addresses  
discovery\_status  
trusted\_device\_count  
active\_transfer\_count  
current\_version

The desktop UI SHOULD render state rather than independently rediscover backend truth.

---

# **133\. System Tray State**

Tray status SHOULD communicate at least:

* ShareBox running;  
* sharing stopped;  
* attention/error required.

The tray icon SHOULD NOT become overloaded with transfer details.

---

# **134\. Firewall Integration**

On Windows, ShareBox may require Windows Defender Firewall permission to accept LAN connections.

The installer/application SHOULD provide the least disruptive safe workflow possible.

Firewall rules SHOULD:

* apply only to the ShareBox executable/service;  
* expose only required ports;  
* prefer private networks where practical;  
* avoid unnecessarily broad rules.

ShareBox MUST NOT disable the firewall.

---

# **135\. Public Network Handling**

Windows distinguishes network profiles such as Private and Public.

ShareBox SHOULD be conservative on Public networks.

At minimum, the desktop application should make it clear when ShareBox is operating on a network considered public/untrusted.

A future hardened implementation MAY automatically restrict sharing under such conditions.

V1 behaviour must be tested before release.

---

# **136\. VPN Handling**

VPN adapters can complicate interface selection.

ShareBox SHOULD avoid advertising an obviously unsuitable VPN address when a normal LAN address is available.

The system MUST NOT assume the first network adapter returned by the operating system is correct.

---

# **137\. Hotspot Behaviour**

ShareBox SHOULD support common hotspot arrangements.

Example:

iPhone hotspot  
    │  
    ├── Windows PC  
    └── another device

or where the phone hosting the hotspot can reach the connected PC.

Actual device isolation behaviour depends on hotspot implementation.

ShareBox documentation must not promise connectivity where the operating system/network prevents peer communication.

---

# **138\. Desktop Folder Change**

When the host changes the ShareBox folder:

1. validate new directory;  
2. verify permissions;  
3. update configuration;  
4. update filesystem watcher;  
5. invalidate stale browser directory state;  
6. expose new root immediately.

Trusted devices remain trusted.

Device upload-folder mappings may need to be recreated lazily within the new root when those devices next upload.

ShareBox MUST NOT silently move all files from the old folder.

---

# **139\. Missing Shared Folder**

If the configured root disappears:

C:\\Users\\John\\ShareBox

ShareBox MUST NOT silently expose a different directory.

Status becomes an actionable error.

The desktop application should offer:

* recreate folder where appropriate;  
* choose another folder.

Browser file operations should remain unavailable until the root is valid.

---

# **140\. Host File Deletion During Download**

If a host file disappears during transfer:

* backend handles filesystem error;  
* connection terminates cleanly;  
* client must not receive a false success state.

ShareBox does not need to lock normal host files merely because they are visible to clients.

---

# **141\. Host File Modification**

If a file changes while being downloaded, exact behaviour may depend on OS/filesystem semantics.

V1 does not guarantee immutable snapshots.

Documentation SHOULD state that ShareBox transfers the host file as available during the operation.

Future integrity/snapshot mechanisms may improve this.

---

# **142\. File Integrity**

Normal HTTP transfer and filesystem error detection provide baseline reliability.

V1 MAY calculate hashes for specific transfer-validation purposes if justified.

ShareBox SHOULD NOT hash every large file unnecessarily merely to display it in the browser.

End-to-end checksums can be evaluated after performance testing.

---

# **143\. Browser Compatibility Target**

V1 MUST target current supported versions of:

* Safari on iOS;  
* Chrome on Android;  
* Chrome/Chromium desktop;  
* Microsoft Edge;  
* Safari on macOS when macOS support ships.

Firefox SHOULD work where standards permit.

The implementation should use standards-based browser APIs rather than browser-specific hacks wherever possible.

---

# **144\. Mobile Browser Constraints**

Design and engineering MUST account for:

* browser suspension;  
* screen locking;  
* mobile OS memory pressure;  
* file picker differences;  
* iOS background restrictions;  
* download behaviour differences;  
* PWA/bookmark differences.

ShareBox MUST NOT promise background-transfer behaviour that mobile browsers cannot reliably provide.

---

# **145\. Browser Session Recovery**

If the browser temporarily loses connection:

CONNECTED  
   ↓  
DISCONNECTED  
   ↓  
RECONNECTING  
   ↓  
CONNECTED

the UI SHOULD attempt recovery without forcing a page reload where practical.

Trusted-device credentials remain valid.

---

# **146\. Unauthorized Browser State**

A browser that reaches ShareBox without authorization must see a controlled ShareBox screen.

It MUST NOT see:

* filenames;  
* folder names;  
* file counts;  
* thumbnails;  
* host filesystem information.

The page may state:

> This device isn't paired with this ShareBox.

and direct the user to pair from the host computer.

---

# **147\. Information Disclosure**

Before authentication, ShareBox SHOULD expose the minimum information required to complete pairing.

Sensitive host details, file metadata and trusted-device information MUST remain protected.

---

# **148\. Hostname and Device Name Privacy**

ShareBox SHOULD avoid unnecessarily exposing the operating-system hostname.

For example, rather than:

DESKTOP-BOLU-PRIVATE-PC

the product may expose:

Bolu's ShareBox

or another ShareBox-specific host display name.

A configurable ShareBox host name MAY be introduced.

---

# **149\. Update Architecture**

V1 packaging SHOULD leave room for application updates.

Because ShareBox is open source, update strategy may eventually support:

* release-page downloads;  
* optional update checks;  
* platform-specific updater mechanisms.

Automatic updates are not required for the initial MVP.

Core operation MUST NOT require an update server.

---

# **150\. Versioning**

ShareBox SHOULD follow semantic versioning once public releases begin:

MAJOR.MINOR.PATCH

Example:

1.2.3

Breaking persistent-state changes require migrations and appropriate version handling.

---

# **151\. Database Migrations**

Persistent database schema changes MUST use explicit migrations.

Code AI MUST NOT assume it can simply delete/recreate the user's local database during upgrades.

Trusted-device relationships should survive normal software updates.

---

# **152\. Configuration Migrations**

Configuration changes must similarly preserve valid existing settings.

If an old setting becomes unsupported, migration behaviour must be explicit.

---

# **153\. Windows Packaging Target**

The Windows release should ultimately provide a conventional installer.

Expected user experience:

Download ShareBox installer  
        ↓  
Run installer  
        ↓  
Install ShareBox  
        ↓  
Launch  
        ↓  
First-time setup

The user MUST NOT need to install separately:

* Python;  
* FastAPI;  
* Node.js;  
* npm;  
* a database;  
* a web server.

All runtime dependencies required by the production application must be packaged appropriately.

---

# **154\. Windows Installation**

The installer should handle:

* application files;  
* required runtime;  
* shortcuts;  
* application-data locations;  
* uninstall registration;  
* firewall integration where appropriate.

Launch-at-startup SHOULD remain a user preference rather than an unavoidable installer side effect.

---

# **155\. Portable Build**

A portable Windows build MAY eventually be provided alongside the installer.

It is not required for the first public V1.

The normal installer remains the primary distribution format.

---

# **156\. macOS Architecture Preparation**

Core code MUST avoid assumptions such as:

C:\\...

or Windows-only path separators.

Filesystem operations must use platform-neutral path APIs.

Future macOS work will require:

* `.app` packaging;  
* menu bar integration;  
* permissions;  
* code signing;  
* notarization;  
* startup behaviour;  
* firewall/network handling.

---

# **157\. Linux Architecture Preparation**

Future Linux support must account for distribution differences.

Potential packaging includes:

* AppImage;  
* `.deb`;  
* other community-supported formats.

Core ShareBox behaviour must not depend on Windows registry or Windows-specific services.

---

# **158\. Testing Architecture**

Testing should be divided into:

Unit Tests  
     ↓  
Service Tests  
     ↓  
API Tests  
     ↓  
Security Tests  
     ↓  
Integration Tests  
     ↓  
Browser Tests  
     ↓  
Platform Tests

Critical filesystem and authentication logic MUST have automated coverage.

---

# **159\. Critical Security Tests**

Tests MUST include attempts involving:

../  
..\\

URL-encoded traversal  
absolute paths  
malformed paths  
symlinks  
duplicate filenames  
malicious filenames  
expired pairing tokens  
reused pairing tokens  
revoked credentials  
missing credentials  
forged device IDs

A release should not rely solely on manual security testing.

---

# **160\. Critical Transfer Tests**

At minimum:

* empty file;  
* tiny text file;  
* image;  
* PDF;  
* video;  
* multi-GB file;  
* Unicode filename;  
* very long filename;  
* duplicate filename;  
* simultaneous uploads;  
* simultaneous download/upload;  
* network interruption;  
* disk-full simulation;  
* host-side deletion during transfer.

---

# **161\. Network Tests**

Testing should cover:

* standard home Wi-Fi;  
* Ethernet host \+ Wi-Fi phone;  
* phone hotspot where peer connectivity permits;  
* IP address change;  
* Wi-Fi reconnect;  
* sleep/wake;  
* port conflict;  
* mDNS unavailable;  
* firewall denial;  
* multiple network adapters.

---

# **162\. V1 Engineering Acceptance Criteria**

Windows V1 is not considered complete until all of the following are true:

1. User can install ShareBox without installing developer dependencies.  
2. ShareBox can create/select its shared folder.  
3. ShareBox starts its LAN service reliably.  
4. User can pair a phone through QR.  
5. Unauthorized devices cannot browse files.  
6. Trusted devices reconnect without pairing again.  
7. Host files are browsable.  
8. Subfolders work.  
9. Files can be downloaded.  
10. Phone files can be uploaded.  
11. Device folder is created only on first upload.  
12. Duplicate uploads do not destroy existing files.  
13. Multi-file uploads work.  
14. Large transfers do not require equivalent RAM.  
15. Revocation removes access.  
16. Path traversal attempts fail.  
17. ShareBox functions without internet.  
18. Host-side filesystem changes appear correctly.  
19. App can run unobtrusively from the tray.  
20. Launch-at-startup works when enabled.  
21. Common network changes do not require reinstalling/re-pairing.  
22. Critical errors are understandable to the user.  
23. Clean uninstall works.  
24. Automated critical-path tests pass.

---

# **163\. Engineering Principle for AI-Generated Code**

ShareBox will likely be developed heavily with AI assistance.

Therefore, generated code MUST be treated as production code requiring architectural discipline.

Code AI MUST NOT:

* duplicate security logic across routes;  
* invent multiple authentication mechanisms;  
* bypass service layers for convenience;  
* use absolute machine-specific paths;  
* expose admin endpoints to LAN clients;  
* disable security to fix development issues;  
* load whole large files into memory;  
* silently catch exceptions;  
* add cloud dependencies;  
* add unnecessary frameworks;  
* rewrite stable architecture merely because a different pattern is easier to generate.

When implementing a feature, Code AI should first identify the existing module responsible for that concern and extend it rather than creating parallel functionality.

---

# **164\. Architectural Decision Records**

Important implementation decisions discovered during development SHOULD be recorded as lightweight ADRs.

Examples:

ADR-001 Desktop UI framework  
ADR-002 Browser credential strategy  
ADR-003 Local transport security  
ADR-004 Filesystem watcher  
ADR-005 Real-time update mechanism  
ADR-006 Windows packaging tool

Each ADR should state:

* decision;  
* context;  
* alternatives considered;  
* rationale;  
* consequences.

This is particularly important because ShareBox is open source and future contributors need to understand **why** architectural choices were made, not merely what the current code happens to do.

---

# **165\. Decisions Requiring Prototype Validation**

The following are intentionally **not falsely locked yet**:

### **Desktop UI framework**

Must be tested for packaging and cross-platform suitability.

### **HTTP vs practical local HTTPS**

Requires technical investigation, particularly around browser trust and certificate UX.

### **Browser credential persistence mechanism**

Must be verified on iOS Safari and Chromium.

### **Filesystem watcher library/implementation**

Must be validated cross-platform.

### **SSE vs polling**

SSE is preferred for evaluation, but reliability should determine the final decision.

### **Packaging tool**

Must be tested against the selected desktop framework and bundled backend.

These decisions should be resolved during the proof-of-concept stage and documented through ADRs.

---

# **166\. Engineering Architecture Summary**

The resulting V1 architecture is:

                    SHAREBOX HOST  
┌─────────────────────────────────────────────────────┐  
│                                                     │  
│ Desktop Control Center                             │  
│        │                                            │  
│        ▼                                            │  
│ Application Services                               │  
│        │                                            │  
│   ┌────┼─────────┬──────────┬────────────┐          │  
│   ▼    ▼         ▼          ▼            ▼          │  
│ Auth  Pairing   Files    Network      Devices       │  
│   │              │                                  │  
│   │              ▼                                  │  
│   │        ShareBox Folder                          │  
│   │                                                 │  
│   └──────────── Backend API                         │  
│                    │                                │  
│              Web Client Assets                      │  
└────────────────────┼────────────────────────────────┘  
                     │  
                     │ Local Network  
                     │  
              ┌──────┴───────┐  
              │              │  
           Browser        Browser  
           iPhone         Android

The fundamental engineering rule remains:

> **ShareBox is a local utility first. The architecture should make local file transfer reliable, secure and nearly invisible—not recreate the complexity of cloud storage software.**

---

**Part III — UX, UI & Design Specification**  
---

# **167\. UX Objective**

ShareBox should make local file transfer feel like a basic capability of the user's devices rather than a technical networking operation.

The primary UX objective is:

> **Once ShareBox has been set up, transferring a file should require almost no thought about ShareBox itself.**

The interface MUST hide unnecessary networking complexity while still exposing useful diagnostic information when something goes wrong.

---

# **168\. UX Principles**

All ShareBox interfaces MUST follow these principles.

### **168.1 Immediate Comprehension**

A user opening any ShareBox screen should quickly understand:

* whether ShareBox is working;  
* what they can do;  
* whether action is required.

### **168.2 Progressive Disclosure**

Technical information such as:

* IP address;  
* port;  
* network interface;  
* discovery status;

should not dominate normal usage.

Expose it where useful for connection troubleshooting or advanced settings.

### **168.3 Low Interaction Cost**

Common actions MUST require fewer interactions than uncommon administrative actions.

For example:

**Open shared folder** should be immediately available.

Changing network configuration can live deeper in Settings.

### **168.4 Calm Utility**

ShareBox should feel dependable and quiet.

Avoid:

* excessive animations;  
* gamification;  
* constant notifications;  
* unnecessary confirmation dialogs;  
* decorative dashboard metrics.

### **168.5 Consistency**

Desktop and web interfaces should clearly belong to the same product while respecting their different purposes.

---

# **169\. Product Personality**

ShareBox should feel:

* simple;  
* fast;  
* trustworthy;  
* modern;  
* private;  
* lightweight;  
* friendly without being playful.

It should NOT feel:

* corporate;  
* highly technical;  
* childish;  
* futuristic for its own sake;  
* like a cloud-storage SaaS dashboard.

---

# **170\. Visual Direction**

The Design AI has freedom to develop the visual identity within the constraints of this specification.

Recommended direction:

* clean surfaces;  
* strong typography hierarchy;  
* moderate corner radii;  
* restrained use of borders;  
* subtle elevation where useful;  
* recognizable icons;  
* generous whitespace;  
* minimal decorative elements.

The design should remain visually strong even without illustrations.

---

# **171\. Color System**

The Design AI should establish semantic color tokens rather than hard-coding colors independently.

At minimum:

Primary  
Background  
Surface  
Surface Secondary  
Text Primary  
Text Secondary  
Border  
Success  
Warning  
Danger  
Info  
Disabled

Status must never depend on color alone.

For example:

● Running

rather than only displaying a green dot without text.

---

# **172\. Light and Dark Mode**

V1 SHOULD support both light and dark appearance if doing so does not materially delay core functionality.

Desktop application SHOULD respect the operating-system preference by default.

The web client SHOULD respect:

prefers-color-scheme

A manual override MAY be provided.

Dark mode is not a release blocker if implementation effort threatens core functionality.

---

# **173\. Typography**

Typography should prioritize readability over branding novelty.

The product SHOULD use:

* a clean sans-serif family;  
* clear hierarchy;  
* comfortable mobile sizes;  
* readable metadata;  
* consistent numeric formatting.

Because ShareBox must work completely offline, required fonts MUST be:

* bundled with the application; or  
* safely provided by the operating system.

The web client MUST NOT depend on Google Fonts or another external font service.

---

# **174\. Iconography**

Icons should be simple and recognizable.

Common concepts include:

* folder;  
* file;  
* image;  
* video;  
* audio;  
* PDF/document;  
* upload;  
* download;  
* search;  
* settings;  
* devices;  
* QR code;  
* network;  
* warning;  
* success;  
* refresh.

Icons MUST NOT be the sole indicator for unfamiliar or destructive actions.

---

# **175\. Motion**

Motion MAY be used for:

* panel transitions;  
* progress;  
* status changes;  
* upload completion;  
* modal appearance.

Motion should be subtle and short.

ShareBox MUST respect reduced-motion preferences where practical.

Decorative animations that delay interaction are prohibited.

---

# **176\. Desktop Information Architecture**

The desktop application should remain compact.

Primary navigation should expose approximately:

Home  
Devices  
Settings

Pairing should be available directly from Home and/or Devices rather than requiring a permanent top-level navigation destination.

The final navigation style may use:

* sidebar;  
* compact tabs;  
* another suitable desktop utility pattern.

Avoid creating navigation sections merely to fill space.

---

# **177\. Desktop Home Screen Purpose**

The Home screen answers four questions:

1. Is ShareBox running?  
2. Which folder am I sharing?  
3. How can I connect another device?  
4. Is anything wrong?

Everything else is secondary.

---

# **178\. Desktop Home — Running State**

Conceptual hierarchy:

┌─────────────────────────────────────────────┐  
│ ShareBox                              ● On  │  
│                                             │  
│ Share files across your local network      │  
│                                             │  
│ Shared Folder                               │  
│ ┌─────────────────────────────────────────┐ │  
│ │ 📁 C:\\Users\\Bolu\\ShareBox              │ │  
│ │                       \[Open Folder\]     │ │  
│ └─────────────────────────────────────────┘ │  
│                                             │  
│ Connect a Device                            │  
│ ┌─────────────────────────────────────────┐ │  
│ │ Scan a QR code to connect another      │ │  
│ │ device.                                │ │  
│ │                                         │ │  
│ │          \[ Pair New Device \]           │ │  
│ └─────────────────────────────────────────┘ │  
│                                             │  
│ 3 trusted devices                          │  
│                                             │  
│                        \[ Stop Sharing \]     │  
└─────────────────────────────────────────────┘

This is structural guidance, not a pixel-level design.

---

# **179\. Service Status Control**

The current service state MUST be immediately visible.

Possible states:

● Sharing  
○ Sharing Off  
\! Attention Required  
◌ Starting

The status control SHOULD allow starting/stopping sharing without entering Settings.

---

# **180\. Shared Folder Component**

The Home screen MUST display the current ShareBox folder.

Primary action:

> Open Folder

Secondary action MAY expose:

> Change Folder

Changing the folder should not be as visually prominent as opening it.

Long paths must truncate gracefully without making the path impossible to inspect.

---

# **181\. Pair New Device Entry Point**

**Pair New Device** MUST be easy to find.

Selecting it opens the pairing experience.

It should not immediately expose technical connection information unless needed.

---

# **182\. Pairing Screen**

Primary content:

Pair a New Device

Scan this QR code with the device  
you want to connect.

        █████████████  
        ██ QR CODE ██  
        █████████████

QR code expires in 03:42

Can't scan the code?  
Show connection details

            \[ Cancel \]

The QR code must receive sufficient physical screen size and contrast for reliable scanning.

---

# **183\. Pairing Expiry**

The UI SHOULD communicate pairing expiry without creating urgency.

Example:

> Code expires in 3:42

When expired:

This pairing code has expired.

\[ Generate New Code \]

Generating another code should require one action.

---

# **184\. Pairing Progress**

After a client opens the QR:

Desktop:

Connecting device…

If additional client identification is required:

New Device

Device name  
\[ Bolu's iPhone              \]

                 \[ Continue \]

Do not ask users to enter technical identifiers.

---

# **185\. Pairing Success**

Success state:

✓ Device Connected

Bolu's iPhone is now trusted.

It can reconnect automatically while  
it can reach this ShareBox.

                    \[ Done \]

The user should not need to perform an additional "save" action.

---

# **186\. Pairing Failure**

Pairing failures must distinguish causes where possible.

Examples:

### **Expired**

> This pairing code has expired.

### **Invalid**

> This pairing link isn't valid.

### **Host unreachable**

> This device couldn't reach ShareBox. Make sure both devices are on the same local network.

Avoid exposing raw socket/network errors to ordinary users.

---

# **187\. Devices Screen**

Purpose:

> Show which devices ShareBox trusts and allow the host to revoke them.

Conceptual structure:

Trusted Devices

┌───────────────────────────────────────┐  
│ 📱 Bolu's iPhone                     │  
│ Last seen: Just now                  │  
│                             \[ ••• \]  │  
├───────────────────────────────────────┤  
│ 📱 Samsung                           │  
│ Last seen: Yesterday                 │  
│                             \[ ••• \]  │  
├───────────────────────────────────────┤  
│ 💻 Office Laptop                     │  
│ Last seen: 4 days ago                │  
│                             \[ ••• \]  │  
└───────────────────────────────────────┘

\[ \+ Pair New Device \]

---

# **188\. Device Information**

For each trusted device, useful information MAY include:

* display name;  
* device-type icon where known;  
* paired date;  
* last seen;  
* current connection state.

Do not display internal device IDs in normal UI.

---

# **189\. Device Rename**

The host SHOULD be able to rename the trusted-device display name.

Example:

Device Name

\[ Bolu's iPhone \]

\[ Save \]

Renaming a device MUST NOT silently rename its existing upload folder as established in Part II.

---

# **190\. Device Revocation**

Revocation is security-sensitive and should require confirmation.

Example:

Remove Bolu's iPhone?

This device will no longer be able to  
access ShareBox. It can be paired again later.

Files previously uploaded by this device  
will remain in your ShareBox folder.

\[ Cancel \]              \[ Remove Device \]

Use clear language rather than "revoke credential" in user-facing copy.

---

# **191\. Settings Screen**

V1 Settings SHOULD contain only meaningful configuration.

Potential groups:

### **General**

* Launch ShareBox at startup  
* Start sharing automatically  
* Appearance, if implemented

### **Shared Folder**

* Current folder  
* Change folder

### **Network**

* connection information;  
* discovery information;  
* advanced network options where required.

### **About**

* version;  
* open-source project/repository access;  
* licenses;  
* update information if supported.

Do not turn Settings into an advanced server administration console.

---

# **192\. Advanced Network Information**

Technical information MAY live under an expandable area:

> Advanced Connection Information

Example:

Local address  
192.168.1.24:8765

Local hostname  
sharebox.local

Network  
Home Wi-Fi

This exists primarily for troubleshooting.

---

# **193\. Change Shared Folder Flow**

Selecting **Change Folder** invokes the operating system's native folder picker where practical.

Before committing, ShareBox MUST validate access.

If changing from an existing root, communicate:

> ShareBox will use this folder from now on. Existing files will not be moved.

Avoid suggesting migration unless migration functionality actually exists.

---

# **194\. Stop Sharing**

Stopping sharing disables LAN client access without quitting ShareBox.

Desktop state becomes:

Sharing is off

Your files aren't currently available  
to other devices.

\[ Start Sharing \]

Trusted-device records remain intact.

---

# **195\. No Network State**

Example:

No Local Network

ShareBox is ready, but this computer isn't  
connected to a local network.

Connect to Wi-Fi or Ethernet to share files.

Do not present this as a catastrophic application error.

---

# **196\. Tray Experience**

Tray menu should provide fast operational controls.

Recommended:

ShareBox — Sharing

Open ShareBox  
Open ShareBox Folder

Pair New Device

Stop Sharing  
──────────────  
Quit ShareBox

When stopped:

ShareBox — Sharing Off

Open ShareBox  
Open ShareBox Folder

Start Sharing  
──────────────  
Quit ShareBox

---

# **197\. Desktop Notifications**

Notifications SHOULD be reserved for useful events.

Appropriate:

* device successfully paired;  
* important transfer failure requiring host attention;  
* ShareBox cannot start;  
* configured folder became unavailable.

Potentially appropriate:

* upload received.

If upload notifications are implemented, users SHOULD be able to disable them.

Do NOT notify for routine:

* browser connections;  
* file browsing;  
* every download;  
* every reconnection.

---

# **198\. First-Run Experience**

First-run setup should be extremely short.

Target:

Welcome  
   ↓  
Shared Folder  
   ↓  
Ready

Pairing a device may be offered immediately afterward but does not need to block setup completion.

---

# **199\. First-Run Screen 1 — Welcome**

Purpose: explain ShareBox in one glance.

Suggested content:

Welcome to ShareBox

Move files between your devices over your  
local network — no cloud required.

\[ Get Started \]

Avoid long feature lists.

---

# **200\. First-Run Screen 2 — Shared Folder**

Suggested:

Choose Your ShareBox Folder

Anything inside this folder can be accessed  
by devices you trust.

○ Create a ShareBox folder for me

○ Choose another folder

\[ Continue \]

The default option SHOULD require minimal effort.

---

# **201\. First-Run Security Communication**

The onboarding should briefly establish:

> Only devices you pair can access your ShareBox.

Do not present a long security tutorial.

Users need the mental model, not implementation details.

---

# **202\. First-Run Completion**

Suggested:

ShareBox is Ready

Your shared folder:  
C:\\Users\\Bolu\\ShareBox

\[ Pair a Device \]

\[ Done \]

Pairing is encouraged but not mandatory.

---

# **203\. Web Client Primary Objective**

The web client exists primarily to answer:

> **What's in my ShareBox, and how do I get something into or out of it?**

Everything else is secondary.

---

# **204\. Web Client Navigation**

The web client should generally use a single primary file-browsing interface rather than desktop-style multi-section navigation.

Avoid a permanent mobile navigation bar unless future features justify one.

V1 essentially has:

ShareBox  
    ↓  
Files/Folders  
    ↓  
Preview / Upload

---

# **205\. Mobile File Browser — Root**

Conceptual structure:

┌──────────────────────────────┐  
│ ShareBox                ●    │  
│                              │  
│ 🔍 Search files              │  
│                              │  
│ Folders                      │  
│                              │  
│ 📁 Projects               ›  │  
│ 📁 Bolu's iPhone          ›  │  
│                              │  
│ Files                        │  
│                              │  
│ 🖼 Screenshot.png         ↓  │  
│    1.8 MB • 2 mins ago       │  
│                              │  
│ 📄 Proposal.pdf           ↓  │  
│    4.2 MB • Yesterday        │  
│                              │  
│                              │  
│        ＋ Upload             │  
└──────────────────────────────┘

Again, structural guidance only.

---

# **206\. Web Header**

The header SHOULD contain:

* ShareBox identity;  
* connection status where useful.

It MAY contain a compact overflow menu for secondary actions.

Avoid filling the header with desktop administration controls.

---

# **207\. Connection Status**

A subtle status indicator MAY show:

● Connected

When disconnected:

○ Reconnecting…

The connection indicator should become visually prominent only when action is required.

---

# **208\. Folder Presentation**

Folders MUST be clearly distinguishable from files.

Selecting a folder navigates into it.

Folder rows/cards should not show download controls unless folder download is explicitly implemented later.

---

# **209\. Folder Breadcrumbs**

Desktop/tablet web layouts SHOULD use breadcrumbs.

Example:

ShareBox › Projects › Glide

On narrow mobile screens, use a compact equivalent such as:

‹ Projects

Glide

The user must never become trapped inside a directory.

---

# **210\. File Rows**

A file row should expose:

* visual type indicator/thumbnail;  
* filename;  
* useful metadata;  
* download action.

Example:

┌────────────────────────────────┐  
│ 🖼  Screenshot.png          ↓  │  
│     1.8 MB • 2 minutes ago     │  
└────────────────────────────────┘

Long filenames should truncate visually while remaining inspectable.

---

# **211\. File Selection Behaviour**

Selecting the file body SHOULD open a preview where supported.

Selecting the download action SHOULD download directly.

For unsupported previews, selecting the file MAY open a detail/download view.

Avoid making users guess whether tapping a filename downloads or previews.

---

# **212\. Image Preview**

Example:

‹ Back

Screenshot.png

┌────────────────────────────┐  
│                            │  
│          IMAGE             │  
│                            │  
└────────────────────────────┘

1.8 MB

\[ Download \]

Image previews should use available viewport space without distorting the image.

---

# **213\. Video Preview**

Use browser-native video playback where supported.

The preview MUST NOT require server-side transcoding in V1.

Unsupported codecs should fall back to download.

---

# **214\. PDF Preview**

PDF may use browser-native capabilities where reliable.

If mobile-browser behaviour is inconsistent, a clear download/open action is preferable to building a custom PDF engine.

---

# **215\. Unsupported File Preview**

Example:

archive.zip

ZIP Archive  
84.7 MB

Preview isn't available for this file.

\[ Download \]

This is not an error state.

---

# **216\. Upload Entry Point**

Upload MUST be one of the most obvious actions in the web interface.

On mobile, a prominent button or floating action may be appropriate.

Example:

＋ Upload

The Design AI may determine the exact placement.

---

# **217\. Mobile Upload Flow**

Selecting Upload opens the device/browser file picker.

Depending on platform this may expose:

* photo library;  
* camera;  
* Files;  
* other storage providers.

ShareBox should use standard browser capabilities rather than recreating the picker.

---

# **218\. Upload Destination Communication**

Because uploads always go into the device's assigned folder, the UI should make this predictable where useful.

Example:

Upload to ShareBox

Files from this device will be saved in:

Bolu's iPhone/

This information need not appear every single time once the mental model is established.

---

# **219\. First Upload**

On first upload, ShareBox creates the device folder automatically.

The client does NOT need to:

* create a folder;  
* choose a destination;  
* approve folder creation.

The experience should simply be:

Choose file  
    ↓  
Upload  
    ↓  
Done

---

# **220\. Upload Queue**

Multiple selected files should appear as a queue/list.

Example:

Uploading 3 files

IMG\_1011.jpg  
████████████████░░ 82%

IMG\_1012.jpg  
████████░░░░░░░░░ 41%

video.mp4  
Waiting…

\[ Cancel \]

Exact concurrency behaviour is determined by the transfer engine.

---

# **221\. Upload Completion**

Successful upload should provide immediate confirmation without interrupting workflow.

Example:

✓ IMG\_1011.jpg uploaded

For multiple files:

> 5 files uploaded.

Avoid mandatory success modals.

---

# **222\. Upload Failure**

Failure should identify the affected file.

Example:

Couldn't upload video.mp4

The connection to ShareBox was interrupted.

\[ Try Again \]

Where retry is safe, provide it.

Do not restart successful files unnecessarily when one item fails.

---

# **223\. Upload Cancellation**

Cancelling an upload should stop incomplete transfers.

If multiple files are queued, the UI SHOULD distinguish:

* cancel individual file;  
* cancel all;

where complexity remains reasonable.

---

# **224\. Search UX**

Search should be immediately accessible near the file list.

Placeholder:

> Search ShareBox

Search results should prioritize matching filename/folder names.

If search covers the entire ShareBox tree, results must show location.

Example:

Screenshot.png  
Projects / Website Assets

---

# **225\. Search Empty State**

Example:

No files found

Nothing in ShareBox matches "invoice".

No unnecessary illustration is required.

---

# **226\. Empty Root State**

For a new ShareBox:

Your ShareBox is empty

Drop files into your ShareBox folder on  
your computer, or upload something from  
this device.

\[ Upload File \]

This teaches the bidirectional mental model.

---

# **227\. Empty Folder State**

Example:

This folder is empty.

Do not imply that the user can upload directly into the currently viewed host folder, because V1 uploads go to the device's assigned folder.

---

# **228\. Unauthorized Web State**

An unpaired browser must receive a branded but minimal page.

Example:

ShareBox

This device isn't connected yet.

Open ShareBox on the host computer and  
choose "Pair New Device" to connect it.

Do not reveal files or device information.

---

# **229\. QR Pairing — Client Side**

After scanning the QR, the browser SHOULD show a clear connection flow.

Example:

Connecting to ShareBox…

Then:

You're Connected

This device can now access ShareBox  
whenever it can reach this computer.

\[ Open ShareBox \]

Pairing should not require account creation.

---

# **230\. Device Name During Pairing**

If ShareBox cannot obtain a useful browser/device label, the client may be asked:

Name This Device

Use a name you'll recognize on your computer.

\[ My iPhone                    \]

\[ Continue \]

This should happen once.

---

# **231\. Revoked Client State**

If the host revokes the device while its browser is open:

Access Removed

This device no longer has access to this  
ShareBox.

Pair it again from the host computer to  
reconnect.

The client must stop displaying previously fetched sensitive data where practical.

---

# **232\. Host Unavailable State**

If the user opens a bookmark while the host is offline, browser behaviour may initially be a native connection failure because the ShareBox server cannot serve UI assets.

Where the web application is already loaded and then loses connectivity, it should display:

Can't Reach ShareBox

The host computer may be asleep, offline,  
or connected to another network.

Trying to reconnect…

The UX specification must acknowledge this technical distinction.

---

# **233\. Reconnection**

When connectivity returns:

Reconnecting…  
      ↓  
Connected

The application SHOULD refresh relevant file state automatically.

A toast MAY say:

> Connected to ShareBox.

Avoid requiring a manual reload.

---

# **234\. Download UX**

For normal downloads, the browser's standard download system SHOULD be used where practical.

ShareBox should not build an unnecessary custom download manager.

The user initiates:

↓ Download

and the browser handles saving/opening according to platform behaviour.

---

# **235\. Download Failure**

If the server can identify a failure before transfer begins:

Couldn't download Screenshot.png

The file may have been moved or deleted  
from the host computer.

\[ Refresh Files \]

---

# **236\. Responsive Web Layout**

The web client MUST adapt across:

### **Small phones**

Single-column list optimized for touch.

### **Large phones/tablets**

Wider list/cards with more metadata.

### **Desktop browsers**

More spacious file browser, potentially including:

* richer breadcrumbs;  
* drag-and-drop;  
* additional metadata columns.

The product should remain recognizably the same application at every breakpoint.

---

# **237\. Desktop Browser Layout**

When another laptop accesses ShareBox, the web client MAY use a file-table layout:

Name                  Size        Modified  
────────────────────────────────────────────  
📁 Projects            —          Today  
📁 Bolu's iPhone       —          Today  
🖼 Screenshot.png     1.8 MB      10:42  
📄 Proposal.pdf       4.2 MB      Yesterday

The Design AI should choose between table/list/card patterns based on viewport.

---

# **238\. Drag-and-Drop Upload**

On compatible desktop browsers, dragging files over the ShareBox interface SHOULD activate a drop target.

Example:

┌────────────────────────────────────┐  
│                                    │  
│       Drop files to upload         │  
│                                    │  
└────────────────────────────────────┘

Files still upload to the authenticated device's assigned folder.

---

# **239\. Touch Targets**

Interactive controls on mobile SHOULD meet modern touch-target recommendations.

Small download icons must have sufficiently large interactive hit areas even if the visual icon itself is compact.

---

# **240\. Loading States**

The UI should distinguish:

### **Initial loading**

ShareBox is fetching file state.

### **Directory loading**

User entered another folder.

### **Transfer state**

Upload/download operation underway.

Use skeletons or subtle progress indicators where useful.

Avoid full-screen loading overlays for routine folder navigation unless necessary.

---

# **241\. Error Philosophy**

Every user-facing error should answer:

1. What happened?  
2. What can the user do?

Bad:

ECONNRESET

Better:

Connection interrupted.

Make sure this device and the host computer  
are still on the same network.

Diagnostic codes MAY be available through expandable technical details.

---

# **242\. Confirmation Philosophy**

Confirmations should be reserved primarily for actions with meaningful consequences.

Examples:

**Require confirmation:**

* revoke trusted device;  
* quit while transfers are active;  
* potentially dangerous configuration change.

**Do not require confirmation:**

* download;  
* upload;  
* open folder;  
* start sharing;  
* generate pairing code.

---

# **243\. Active Transfer \+ Host Quit**

If the host attempts to quit ShareBox while transfers are active:

Transfers Are Still Running

2 transfers will be interrupted if you quit.

\[ Keep ShareBox Running \]

\[ Quit Anyway \]

Stopping sharing during active transfers should use similarly explicit behaviour.

---

# **244\. File Type Icons**

ShareBox should provide broad recognizable categories rather than maintaining thousands of proprietary application icons.

Recommended categories:

Folder  
Image  
Video  
Audio  
PDF  
Document  
Spreadsheet  
Presentation  
Archive  
Code/Text  
Unknown File

Thumbnails may replace generic icons for supported images.

---

# **245\. Thumbnail Behaviour**

Image thumbnails SHOULD be generated or served efficiently.

The interface MUST NOT download a full multi-megabyte image merely to display a tiny thumbnail if a lightweight thumbnail strategy is practical.

Thumbnail generation must remain optional enough that failure does not prevent normal file browsing.

---

# **246\. Filename Handling**

The UI must gracefully support:

* long names;  
* spaces;  
* Unicode;  
* emoji;  
* multiple extensions;  
* extensionless files.

Never assume filenames are ASCII.

Long names should truncate with access to the full name via appropriate interaction.

---

# **247\. Time Display**

User-facing timestamps SHOULD use friendly local formatting.

Examples:

Just now  
2 minutes ago  
Today, 9:42 AM  
Yesterday  
Aug 4

Exact dates/times may be available where useful.

Backend/API timestamps should remain standardized independently.

---

# **248\. File Size Display**

Use human-readable sizes:

842 KB  
1.8 MB  
4.2 GB

Avoid raw byte counts in normal UI.

---

# **249\. Host Display Name**

The web interface SHOULD identify which ShareBox instance it is connected to if needed.

Example:

Bolu's ShareBox

This becomes particularly useful if a user eventually interacts with multiple ShareBox hosts.

A default may be generated during setup.

---

# **250\. Security UX**

Security should feel understandable rather than intimidating.

Use:

> Trusted Devices

instead of:

> Authorized Client Credentials

Use:

> Remove Device

instead of:

> Revoke Authentication Token

Use:

> Pair New Device

instead of:

> Initiate Authentication Exchange

Technical terminology belongs in documentation and diagnostics, not normal UI.

---

# **251\. Privacy Messaging**

Where product messaging discusses privacy, claims must be precise.

Appropriate:

> Files are transferred directly over your local network. ShareBox doesn't require cloud storage.

Avoid absolute claims such as:

> Impossible for anyone to intercept.

The actual transport-security limitations defined in Part II must be respected.

---

# **252\. Offline UX**

ShareBox should not display:

> You're offline.

merely because the internet is unavailable.

If LAN connectivity works, ShareBox is operational.

The relevant concept is:

Can client reach ShareBox host?

not:

Can client reach internet?

This distinction is fundamental.

---

# **253\. Design Tokens**

Design AI SHOULD establish reusable tokens for:

Color  
Typography  
Spacing  
Radius  
Elevation  
Motion  
Breakpoints  
Icon sizing  
Control sizing

Implementation SHOULD consume these tokens rather than creating arbitrary values throughout the codebase.

---

# **254\. Core Components — Desktop**

Design AI should define reusable components for at least:

* application navigation;  
* status badge;  
* primary button;  
* secondary button;  
* destructive button;  
* folder field/card;  
* device card/row;  
* QR panel;  
* settings row;  
* toggle;  
* modal;  
* toast;  
* error banner;  
* empty state;  
* tooltip;  
* dropdown/context menu.

---

# **255\. Core Components — Web**

Define:

* web header;  
* search field;  
* breadcrumb;  
* folder row;  
* file row;  
* thumbnail;  
* file-type icon;  
* download control;  
* upload button;  
* upload queue item;  
* progress indicator;  
* toast;  
* preview container;  
* empty state;  
* connection-state banner;  
* unauthorized state.

Components should share visual language with desktop where sensible.

---

# **256\. Destructive Action Styling**

Destructive visual styling is reserved for genuinely destructive/security-impacting actions.

Examples:

* Remove Device  
* Quit during active transfer

Routine controls should not use danger styling.

---

# **257\. Toasts**

Toasts are appropriate for transient feedback:

✓ File uploaded  
✓ Device connected  
\! Upload failed

They should:

* disappear automatically when appropriate;  
* remain long enough to read;  
* not obscure primary controls;  
* support accessibility announcements.

Persistent problems require persistent UI, not disappearing toasts.

---

# **258\. Modal Usage**

Use modals for focused temporary tasks such as:

* revocation confirmation;  
* pairing;  
* device rename;  
* active-transfer quit warning.

Do not turn every action into a modal.

---

# **259\. Desktop Window Behaviour**

The main desktop window SHOULD remember sensible window state where appropriate.

It should have a reasonable minimum size.

The layout must remain usable when resized within supported limits.

Closing the window hides it to tray if ShareBox remains active.

The first time this happens, ShareBox MAY briefly explain:

> ShareBox is still running in the background.

Do not show this repeatedly.

---

# **260\. Keyboard Accessibility**

Desktop and desktop-web interfaces SHOULD support:

* Tab navigation;  
* Enter/Space activation;  
* Escape to close modal where appropriate;  
* logical focus order.

File browser keyboard shortcuts MAY be added later but are not required for V1.

---

# **261\. Screen Reader Accessibility**

Controls MUST have meaningful accessible labels.

Bad:

\<button\>↓\</button\>

Accessible intent:

> Download Screenshot.png

Status changes such as upload completion SHOULD be announced appropriately.

---

# **262\. Focus Management**

When a modal opens, focus should move into it.

When it closes, focus should return to the invoking control.

Pairing and error-state transitions should maintain sensible focus.

---

# **263\. Design AI Deliverables**

The Design AI should produce, at minimum:

### **A. Visual Foundation**

* color system;  
* typography;  
* spacing;  
* radii;  
* elevation;  
* icon approach;  
* light/dark treatment where applicable.

### **B. Desktop Application**

Complete designs for all screens/states defined in this specification.

### **C. Mobile Web Client**

Complete phone layouts and states.

### **D. Responsive Web**

Tablet and desktop behaviour.

### **E. Component Library**

Reusable components with:

* default;  
* hover where applicable;  
* focus;  
* active;  
* disabled;  
* loading;  
* error states.

### **F. Interaction Specification**

Important transitions and behaviour.

---

# **264\. Design AI Freedom**

The Design AI MAY decide:

* exact colors;  
* typography family;  
* spacing scale;  
* layout proportions;  
* icon set;  
* visual treatment;  
* navigation pattern;  
* component styling;  
* appropriate micro-animation.

It MUST NOT independently change:

* product functionality;  
* security model;  
* permission model;  
* upload destination behaviour;  
* pairing model;  
* desktop/web responsibility split;  
* V1 scope.

Design must serve the product architecture rather than redefine it.

---

# **265\. Design AI Anti-Patterns**

Do NOT produce ShareBox as:

### **A cloud-storage clone**

Avoid unnecessary:

Storage used: 7.2 GB / 100 GB  
Upgrade Plan  
Billing  
Team Members

ShareBox has no cloud quota or subscription in V1.

### **An analytics dashboard**

Avoid meaningless:

Files transferred this month  
Transfer growth  
Usage chart

unless such data becomes a real future requirement.

### **A server admin panel**

Avoid placing:

0.0.0.0  
TCP  
PID  
Interface eth0

on Home.

### **A mobile file-manager replacement**

Client users are intentionally not managing the host filesystem.

---

# **266\. Recommended Desktop Home Priority**

Visual priority should approximately be:

1\. SHAREBOX STATUS

2\. SHARED FOLDER

3\. PAIR DEVICE

4\. DEVICE SUMMARY

5\. SECONDARY CONTROLS

The user should not have to hunt for the first three.

---

# **267\. Recommended Mobile Priority**

Visual priority:

1\. CURRENT LOCATION

2\. FILES / FOLDERS

3\. UPLOAD

4\. SEARCH

5\. CONNECTION / SECONDARY INFO

Depending on final layout, Search may move higher without violating the intent.

---

# **268\. Common Everyday Workflow — PC to Phone**

The final design MUST make this possible:

### **First time**

Install ShareBox  
      ↓  
Choose folder  
      ↓  
Pair phone  
      ↓  
Done

### **Every subsequent time**

Save file to ShareBox folder  
      ↓  
Open ShareBox on phone  
      ↓  
Tap Download

The desktop control center does not need to be opened.

---

# **269\. Common Everyday Workflow — Phone to PC**

After pairing:

Open ShareBox on phone  
      ↓  
Tap Upload  
      ↓  
Choose file(s)  
      ↓  
Upload  
      ↓  
File appears in:  
ShareBox/\[Device Folder\]/

No destination selection is required.

---

# **270\. Design Success Criterion**

The design succeeds when a user can understand ShareBox without needing to understand its architecture.

A new user should infer:

> **"This folder is available to my trusted devices, and I can also send files back into it."**

without needing explanation of:

* HTTP;  
* LAN addressing;  
* FastAPI;  
* ports;  
* mDNS;  
* authentication tokens.

---

# **271\. UX Acceptance Criteria**

The V1 design is complete only when:

1. Every defined desktop state has a design.  
2. Every defined web state has a design.  
3. Pairing is fully designed on both host and client.  
4. First-run setup is complete.  
5. Upload flow is complete.  
6. Download behaviour is unambiguous.  
7. Trusted-device management is complete.  
8. Failure states are designed.  
9. Mobile layout works on narrow screens.  
10. Desktop browser layout is defined.  
11. Empty states are defined.  
12. Loading states are defined.  
13. Accessibility states are accounted for.  
14. Destructive actions are clearly differentiated.  
15. Technical information is progressively disclosed.  
16. No V1 feature requires internet access because of its UI implementation.  
17. The interface does not introduce functionality outside the product specification.

---

# **272\. Design Handoff Requirements**

Design handoff to Code AI should include:

* screen designs;  
* component specifications;  
* responsive behaviour;  
* design tokens;  
* typography scale;  
* spacing scale;  
* icon references;  
* interaction states;  
* loading states;  
* error states;  
* empty states;  
* hover/focus states;  
* relevant motion specifications.

Code AI should not need to guess important interaction behaviour from static screenshots alone.

---

# **273\. UX Copy Principle**

ShareBox copy should be:

* short;  
* specific;  
* calm;  
* action-oriented.

Prefer:

> Can't reach the host computer.

over:

> An unexpected network connectivity error has occurred.

Prefer:

> Pair New Device

over:

> Add Authorized Network Client

Prefer:

> Open Folder

over:

> Navigate to Shared Directory

---

# **274\. Cross-Platform Design Adaptation**

ShareBox should maintain one visual identity across operating systems without forcing every platform to behave identically.

Platform-native conventions SHOULD be respected for:

* window behaviour;  
* menu bar/system tray;  
* folder pickers;  
* notifications;  
* keyboard conventions;  
* installation.

The product should feel like **ShareBox on Windows**, **ShareBox on macOS**, and **ShareBox on Linux**, rather than a Windows application awkwardly ported everywhere.

---

# **275\. Part III Final Design Principle**

Every ShareBox design decision should be tested against one question:

> **Does this make moving a file between nearby devices simpler?**

If a UI element, screen, animation, setting or interaction does not contribute to:

* transferring files;  
* establishing trust;  
* understanding status;  
* configuring necessary behaviour;  
* recovering from failure;

it probably does not belong in ShareBox V1.

---

### **Part IV — Implementation, Release & Final Requirements**

---

# **276\. Development Strategy**

ShareBox MUST be developed incrementally.

The Code AI must not attempt to generate the entire production application in one pass.

Each development phase must:

1. have a defined objective;  
2. produce working software;  
3. be tested before proceeding;  
4. preserve architecture established in Parts I–III.

The development priority is:

> **Working transfer engine → security → usable interface → desktop integration → packaging → hardening.**

Visual polish must never be used to compensate for an unreliable core.

---

# **277\. Phase 0 — Technical Proof of Concept**

## **Objective**

Prove that ShareBox's fundamental architecture works before building the actual product UI.

Build the smallest possible implementation capable of:

Windows PC

    │

    │ Local Wi-Fi

    ▼

Phone Browser

### **Required**

* FastAPI local server;  
* configurable shared folder;  
* directory listing;  
* subfolder navigation;  
* PC → phone download;  
* phone → PC upload;  
* LAN access from Android;  
* LAN access from iPhone;  
* operation without internet.

### **Not Required**

* polished UI;  
* desktop application;  
* pairing;  
* trusted devices;  
* system tray;  
* mDNS;  
* installer.

### **Exit Gate**

Do not proceed until:

> A real Android and iPhone on the same LAN can browse, download and upload files reliably.

This phase should also validate the fundamental browser/network assumptions made in this specification.

---

# **278\. Phase 1 — File Transfer Core**

Convert the prototype into a structured backend.

Implement:

* filesystem service;  
* path-security service;  
* directory API;  
* download streaming;  
* upload streaming;  
* per-device upload architecture;  
* lazy device-folder creation;  
* filename collision handling;  
* temporary upload files;  
* search;  
* file metadata;  
* error model;  
* concurrent transfers.

### **Required Tests**

* path traversal;  
* large files;  
* duplicate filenames;  
* Unicode filenames;  
* interrupted upload;  
* concurrent transfers;  
* storage failure;  
* subfolders.

### **Exit Gate**

The transfer engine must be reliable and filesystem-safe before authentication/UI complexity is added.

---

# **279\. Phase 2 — Device Trust & Pairing**

Implement:

* host identity;  
* device identity;  
* trusted-device storage;  
* pairing sessions;  
* QR pairing;  
* pairing expiry;  
* single-use pairing tokens;  
* persistent client authentication;  
* automatic reconnection;  
* device revocation;  
* unauthorized state;  
* security logging.

This phase MUST validate the chosen browser credential mechanism on:

* iOS Safari;  
* Android Chrome;  
* desktop Chromium.

The transport-security investigation defined in Part II should also be completed here and recorded as an ADR.

### **Exit Gate**

An unknown device cannot browse ShareBox.

A paired device can return later without pairing again.

A revoked device immediately loses access.

---

# **280\. Phase 3 — Production Web Client**

Replace prototype HTML with the proper ShareBox web interface defined in Part III.

Implement:

* responsive file browser;  
* folder navigation;  
* breadcrumbs;  
* search;  
* file-type representation;  
* previews;  
* downloads;  
* upload flow;  
* multi-file uploads;  
* upload queue;  
* progress;  
* retry/error states;  
* empty states;  
* unauthorized state;  
* connection/reconnection state;  
* desktop drag-and-drop;  
* accessibility requirements.

All frontend assets MUST work without internet connectivity.

### **Exit Gate**

A phone user should be able to use ShareBox without technical explanation.

---

# **281\. Phase 4 — Desktop Control Center**

Build the Windows desktop application.

Implement:

* Home;  
* service status;  
* start/stop sharing;  
* shared-folder controls;  
* Pair New Device;  
* QR presentation;  
* Devices;  
* rename device;  
* revoke device;  
* Settings;  
* error states;  
* network information;  
* first-run onboarding.

The desktop application must control the existing backend rather than reimplement backend logic.

### **Exit Gate**

A new user can configure and operate ShareBox entirely through the desktop UI.

No terminal is required.

---

# **282\. Phase 5 — Windows Integration**

Implement:

* system tray;  
* background operation;  
* launch at startup;  
* native folder picker;  
* open-folder action;  
* notifications;  
* firewall integration;  
* network profile handling;  
* sleep/wake recovery;  
* network-change recovery;  
* clean shutdown.

Test with ordinary Windows user permissions.

### **Exit Gate**

After initial configuration:

Start PC

   ↓

ShareBox starts quietly

   ↓

Phone joins same LAN

   ↓

Open ShareBox

   ↓

Files available

No terminal, server command or manual initialization is required.

---

# **283\. Phase 6 — Packaging**

Produce a standalone Windows distribution.

The user MUST NOT need:

* Python;  
* pip;  
* Node.js;  
* npm;  
* FastAPI installation;  
* database installation;  
* developer tools.

Provide a normal installer.

Test:

* fresh installation;  
* upgrade;  
* launch;  
* firewall behaviour;  
* startup;  
* uninstall;  
* reinstall;  
* preservation/migration of appropriate user configuration.

### **Exit Gate**

ShareBox can be installed on a clean supported Windows computer and works as specified.

---

# **284\. Phase 7 — Hardening**

Before public V1:

### **Security**

* rerun traversal tests;  
* authentication tests;  
* pairing replay tests;  
* revocation tests;  
* malicious filename tests;  
* symlink tests;  
* unauthorized API tests.

### **Reliability**

* multi-GB transfers;  
* multiple clients;  
* Wi-Fi interruption;  
* host sleep/wake;  
* IP changes;  
* disk-full condition;  
* long-running application session;  
* rapid start/stop;  
* interrupted uploads.

### **UX**

Test actual workflows on:

* iPhone;  
* Android;  
* Windows browser;  
* different screen sizes.

Fix critical and high-severity issues before release.

---

# **285\. Phase 8 — Open-Source Release**

Prepare the public repository.

Required root documentation:

README.md

LICENSE

CONTRIBUTING.md

SECURITY.md

CHANGELOG.md

Repository should also include:

docs/

tests/

and the appropriate source/build structure established during implementation.

---

# **286\. README Requirements**

The README should quickly explain:

### **What ShareBox is**

> ShareBox lets you move files between devices on the same local network using a shared folder and a web browser. No cloud storage or mobile app is required.

### **How it works**

Install ShareBox on computer

        ↓

Pair another device

        ↓

Open ShareBox in browser

        ↓

Upload / Download

Also include:

* supported platforms;  
* installation;  
* screenshots;  
* development setup;  
* build instructions;  
* security/privacy overview;  
* contribution link.

Do not make the README a duplicate of this master specification.

---

# **287\. Open-Source License**

A permissive open-source license SHOULD be selected unless project goals later require otherwise.

MIT or Apache 2.0 are appropriate candidates.

The final license choice should be made before public release and dependency licenses checked for compatibility.

---

# **288\. Contribution Requirements**

External contributions must preserve ShareBox's product philosophy.

Contributors should not introduce:

* mandatory cloud services;  
* telemetry without approval;  
* unrelated features;  
* unnecessary heavy dependencies;  
* security bypasses;  
* platform-specific assumptions inside core logic.

Major features should be discussed before implementation.

---

# **289\. Security Reporting**

`SECURITY.md` MUST provide a responsible method for privately reporting security vulnerabilities.

Security vulnerabilities SHOULD NOT require public disclosure through a normal GitHub issue before maintainers have an opportunity to address them.

---

# **290\. Release Priority**

For V1, priorities are strictly:

1\. Security

2\. Reliability

3\. Correctness

4\. Ease of use

5\. Performance

6\. Visual polish

7\. Additional features

A release must not ship a known serious security or data-loss issue merely to meet a schedule.

---

# **291\. V1 Definition of Done**

ShareBox V1 is complete when a nontechnical Windows user can:

1. Download and install ShareBox.  
2. Launch it without developer tools.  
3. Select or accept a ShareBox folder.  
4. Pair an iPhone or Android device using QR.  
5. Reconnect that device automatically later.  
6. Place files in the PC ShareBox folder.  
7. Browse those files from the phone.  
8. Navigate subfolders.  
9. Search files.  
10. Preview supported files.  
11. Download files.  
12. Upload one or multiple phone files.  
13. Find uploaded files inside that device's automatically created folder.  
14. Use ShareBox without internet connectivity.  
15. Manage trusted devices.  
16. Revoke a device.  
17. Start/stop sharing.  
18. Run ShareBox in the background.  
19. Launch ShareBox automatically with Windows when enabled.  
20. Recover from normal network changes without reconfiguration.

Additionally:

* unauthorized devices cannot access shared content;  
* clients cannot escape the ShareBox filesystem boundary;  
* browser clients cannot delete/rename host files;  
* duplicate uploads cannot silently overwrite existing files;  
* large transfers are streamed;  
* critical failures are handled clearly;  
* core functionality has automated tests.

---

# **292\. Explicit V1 Exclusions**

The following MUST remain outside the initial release unless this specification is deliberately revised:

* clipboard sharing;  
* text/link sharing;  
* cloud synchronization;  
* remote internet access;  
* accounts;  
* browser deletion;  
* browser rename/move;  
* native mobile applications;  
* direct client-to-client transfer;  
* transfer analytics;  
* storage quotas;  
* collaborative features.

These are roadmap candidates, not unfinished V1 requirements.

---

# **293\. Post-V1 Platform Expansion**

After Windows V1 is stable:

### **macOS**

Adapt:

* packaging;  
* menu bar;  
* startup;  
* permissions;  
* firewall/network behaviour;  
* signing/notarization.

Core transfer and web logic SHOULD remain substantially unchanged.

### **Linux**

Adapt:

* packaging;  
* tray integration;  
* startup;  
* filesystem/platform conventions;  
* distribution-specific concerns.

Cross-platform expansion should reveal platform abstractions that need improvement, not trigger a complete rewrite.

---

# **294\. Future Product Direction**

ShareBox may eventually evolve from a local file utility into a broader **cross-device continuity utility**.

Potential progression:

V1

Files

 │

 ▼

V2+

Files \+ Clipboard

 │

 ▼

Files \+ Clipboard \+ Text \+ Links

However:

> Future possibilities MUST NOT make V1 unnecessarily complex.

The immediate product wins by doing one thing extremely well:

**moving files between nearby devices.**

---

# **295\. Final Instructions to Design AI**

Before designing ShareBox:

1. Read Parts I and III completely.  
2. Use Part II where technical constraints affect UX.  
3. Treat V1 scope as fixed.  
4. Design the complete system rather than isolated attractive screens.  
5. Include loading, empty, error and disconnected states.  
6. Preserve mobile-first web usability.  
7. Keep the desktop application compact.  
8. Do not invent cloud/account functionality.  
9. Deliver reusable components and design tokens.  
10. Flag genuine specification conflicts instead of silently redesigning the product.

The objective is not to make ShareBox look complicated enough to appear powerful.

The objective is to make a technically capable product feel extremely simple.

---

# **296\. Final Instructions to Code AI**

Before writing production code:

1. Read all four parts of this specification.  
2. Understand the architecture before generating files.  
3. Follow the implementation phases in order.  
4. Do not skip the proof of concept.  
5. Do not compromise filesystem security.  
6. Do not introduce cloud dependencies.  
7. Keep desktop, backend, web and platform responsibilities separated.  
8. Write tests alongside critical functionality.  
9. Record major implementation decisions as ADRs.  
10. Stop and flag genuine architectural conflicts rather than silently deviating from the specification.

Code should be optimized for:

* readability;  
* maintainability;  
* testability;  
* security;  
* cross-platform evolution.

Not for minimum generated line count or fastest possible initial implementation.

---

# **297\. Source of Truth**

This four-part specification is the authoritative product definition for ShareBox V1.

The hierarchy is:

Master Specification

        │

        ├── Part I

        │   Product & Requirements

        │

        ├── Part II

        │   Engineering Architecture

        │

        ├── Part III

        │   UX & Design

        │

        └── Part IV

            Implementation & Release

Design files, implementation plans, AI prompts, tickets and code must conform to this specification.

When implementation reveals that a requirement needs to change, the specification should be updated rather than allowing the code and documentation to silently diverge.

---

# **298\. Final Product Definition**

**ShareBox is an open-source, local-first file sharing utility that turns a folder on a host computer into a secure shared space accessible from trusted devices on the same local network through their web browsers.**

It requires no cloud storage, no mobile application and no internet connection for core file transfers.

The host computer runs a lightweight desktop control application and local server.

Trusted devices can:

**Browse → Navigate → Search → Preview → Download → Upload.**

They cannot modify or delete existing host files.

Uploads are automatically organized into lazily created device-specific folders.

Devices are initially paired using QR codes, remembered afterward and automatically recognized when they reconnect. The host retains complete control over trusted devices and may revoke access at any time.

Windows is the first release platform, while the architecture is designed for subsequent macOS and Linux support.

The defining experience is simple:

> **Put something in ShareBox on one device. Pick it up from another.**

---

