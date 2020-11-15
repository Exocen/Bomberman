const NO_CONNECTION_MESSAGE = 'Disconnected';
const ADDRESS = 'localhost';
const PORT = 5678;
const TITLE = 'Bomberman demo';
const BOMB1 = 'imgs/bomb1.png';
const BOMB2 = 'imgs/bomb2.png';
const BOOM1 = 'imgs/boom1.png';
const BOOM2 = 'imgs/boom2.png';
const BOOM3 = 'imgs/boom3.png';
const GRASS1 = 'imgs/grass1.png';
const WALL1 = 'imgs/wall1.png';
const BOMB_OK = 'imgs/bomb_ok.png';
const BOMB_NOK = 'imgs/bomb_nok.png';
const USER1 = 'imgs/user1.png';
const USER2 = 'imgs/user2.png';
const USER3 = 'imgs/user3.png';
const USER4 = 'imgs/user4.png';
const MAX_LOG = 20;

class WebSocketClient {
    address;
    port;
    options;
    ws;
    tmp_data;

    constructor(address, port, options) {
        this.address = address;
        this.port = port;
        this.options = options;

        this.connect();
    }

    connect() {
        this.ws = new WebSocket(`ws://${this.address}:${this.port}/`);

        this.ws.onclose = () => {
            this.onClose();
        };
        this.ws.onmessage = (e) => {
            this.onMessage(e);
        };
    }

    getState() {
        return this.ws.readyState;
    }

    send(data) {
        this.ws.send(JSON.stringify(data));
    }

    onClose() {}

    onMessage(e) {
        const data = JSON.parse(e.data);
        // Todo should add a debug option for logs
        // console.log(data)

        switch (data.type) {
            case 'init':
                if (
                    !this.id &&
                    this.options.onInit && {}.toString.call(this.options.onInit) === '[object Function]'
                ) {
                    this.options.onInit(data);
                    this.id = data.id;
                }
                break;
            case 'map':
                if (
                    this.id &&
                    this.options.onMap && {}.toString.call(this.options.onMap) === '[object Function]'
                )
                    this.options.onMap(data);
                break;

            case 'log':
                if (
                    this.id &&
                    this.options.onLog && {}.toString.call(this.options.onLog) === '[object Function]'
                )
                    this.options.onLog(data);
                break;

            default:
                console.error(`Unsupported event : ${data}`);
                break;
        }
    }
}

class Controls {
    constructor(wsClient) {
        this.wsClient = wsClient;
        this.addListener();
    }

    addListener() {
        // Prevent moving windows with keys
        window.addEventListener(
            'keydown',
            function(e) {
                // space and arrow keys
                if ([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
                    e.preventDefault();
                }
            },
            false
        );

        document.body.addEventListener('keyup', (e) => {
            this.onKeyUp(e);
        });
        document.getElementById('console').addEventListener('keyup', (e) => {
            this.chat(e);
        });

        document.getElementById('bomb').addEventListener('click', (e) => {
            this.onClick(e);
        });
        document.getElementById('left').addEventListener('click', () => {
            this.onKeyUp({
                keyCode: 37
            });
        });
        document.getElementById('up').addEventListener('click', () => {
            this.onKeyUp({
                keyCode: 38
            });
        });
        document.getElementById('right').addEventListener('click', () => {
            this.onKeyUp({
                keyCode: 39
            });
        });
        document.getElementById('down').addEventListener('click', () => {
            this.onKeyUp({
                keyCode: 40
            });
        });
    }

    onKeyUp(e) {
        if (this.wsClient.getState() !== WebSocket.OPEN) return;

        let action = '';
        let console = document.getElementById('console');
        if (console === document.activeElement) {
            return;
        }

        switch (e.keyCode) {
            case 32:
                action = 'bomb';
                break;
            case 37:
                action = 'left';
                break;
            case 38:
                action = 'up';
                break;
            case 39:
                action = 'right';
                break;
            case 40:
                action = 'down';
                break;
            default:
                return;
        }

        this.Move(action);
        this.wsClient.send({
            action
        });
    }

    Move(e) {
        let control = document.getElementById(e);
        control.classList.remove(e);
        void control.offsetWidth;
        control.classList.add(e);
    }

    onClick(e) {
        this.wsClient.send({
            action: 'bomb'
        });
    }

    chat(e) {
        if (e.keyCode == 13) {
            let console = document.getElementById('console');
            let chat = console.value;
            this.wsClient.send({
                chat
            });
            console.value = '';
        }
    }
}

class Game {
    height;
    width;

    constructor(height = 0, width = 0, options = {}) {
        this.height = height;
        this.width = width;

        this.ws = new WebSocketClient(
            options.address || ADDRESS,
            options.port || PORT, {
                onInit: (data) => {
                    this.onInit(data);
                },
                onMap: (data) => {
                    this.onMap(data);
                },
                onLog: (data) => {
                    this.onLog(data);
                },
            }
        );
        this.controls = new Controls(this.ws);
    }

    getDOMElement() {
        return document.getElementById('gameboard');
    }

    resize(height, width) {
        this.height = height;
        this.width = width;

        this.draw();
    }

    draw() {
        for (var i = 0; i < this.height; i++) {
            var line = document.createElement('div');
            line.classList.add('line');

            for (var j = 0; j < this.width; j++) {
                var cell = document.createElement('div');
                cell.classList.add('cell');

                line.appendChild(cell);
            }

            this.getDOMElement().appendChild(line);
        }
    }

    replaceImgSrc(img, src) {
        if (img.src.split('/').reverse()[0] !== src.split('/').reverse()[0]) {
            img.src = src;
        }
    }

    drawExplosions(explosions) {
        const boardElement = this.getDOMElement();
        let lines = boardElement.getElementsByClassName('line');

        explosions.forEach((explosion) => {
            let src = BOOM1;

            if (explosion.direction === 'v') {
                src = BOOM2;
            }

            if (explosion.direction === 'h') {
                src = BOOM3;
            }

            if (explosion.dead) {
                src = GRASS1;
            }

            let line = lines.item(explosion.y);

            if (!line) return;

            let cells = line.getElementsByClassName('cell');
            let cell = cells.item(explosion.x);

            if (!cell) return;

            this.replaceImgSrc(cell.childNodes[0], src);
        });
    }

    getUser(mod) {
        if (isNaN(mod)) {
            return;
        }

        let src;

        switch (mod) {
            case 1:
                src = USER1;
                break;
            case 2:
                src = USER2;
                break;
            case 3:
                src = USER3;
                break;
            case 4:
                src = USER4;
                break;
            default:
                return;
        }
        return src;
    }

    drawBombs(bombs) {
        const boardElement = this.getDOMElement();
        let lines = boardElement.getElementsByClassName('line');

        bombs.forEach((bomb) => {
            let src = BOMB1;

            if (bomb.bomb_state === 2) {
                src = BOMB2;
            } else if (bomb.bomb_state === 3) {
                src = BOOM1;
            }

            if (bomb.dead) {
                src = GRASS1;
            }

            let line = lines.item(bomb.y);

            if (!line) return;

            let cells = line.getElementsByClassName('cell');
            let cell = cells.item(bomb.x);

            if (!cell) return;

            this.replaceImgSrc(cell.childNodes[0], src);
        });
    }

    drawGrass(grasss) {
        const boardElement = this.getDOMElement();
        let lines = boardElement.getElementsByClassName('line');

        grasss.forEach((grass) => {
            let src = GRASS1;

            let line = lines.item(grass.y);

            if (!line) return;

            let cells = line.getElementsByClassName('cell');
            let cell = cells.item(grass.x);

            if (!cell) return;
            this.replaceImgSrc(cell.childNodes[0], src);
        });
    }

    drawWalls(walls) {
        const boardElement = this.getDOMElement();
        let lines = boardElement.getElementsByClassName('line');

        walls.forEach((wall) => {
            let src = WALL1;

            if (wall.dead) {
                src = GRASS1;
            }

            let line = lines.item(wall.y);

            if (!line) return;

            let cells = line.getElementsByClassName('cell');
            let cell = cells.item(wall.x);

            if (!cell) return;
            this.replaceImgSrc(cell.childNodes[0], src);
        });
    }

    drawUsers(users) {
        const boardElement = this.getDOMElement();
        let lines = boardElement.getElementsByClassName('line');

        users.forEach((user) => {
            if (user.id === this.ws.id) {
                let game_status = document.getElementById('gamestatus');
                game_status.innerHTML = '';
                let img = document.createElement('img');

                img.src = this.getUser(user.mod);
                // Todo bad spacing here, use css
                let textnode = document.createTextNode(
                    ` killed:${user.killed} deaths:${user.deaths} suicides:${user.suicides}`
                );
                game_status.appendChild(img);
                game_status.appendChild(textnode);

                let bombDropElement = document.getElementById('bomb').childNodes[0];
                let src = BOMB_NOK;

                if (user.can_drop) src = BOMB_OK;
                this.replaceImgSrc(bombDropElement, src);
            }

            let line = lines.item(user.y);

            if (!line) return;

            let cells = line.getElementsByClassName('cell');
            let cell = cells.item(user.x);

            if (!cell) return;

            let src = this.getUser(user.mod);

            this.replaceImgSrc(cell.childNodes[0], src);
        });
    }

    cleanBoard() {
        const cells = document.getElementsByClassName('cell');

        for (var i = 0; i < cells.length; i++) {
            let cell = cells.item(i);
            let grassImage = new Image();
            grassImage.src = GRASS1;

            cell.style.backgroundColor = '';
            cell.innerHTML = '';
            cell.appendChild(grassImage);
        }
    }

    onInit(data) {
        this.resize(data.length, data.width);
        this.cleanBoard();
        this.onMap(data);
    }

    onLog(data) {
        // Todo find a better message struct and stop parsing
        // [{'type:data'},{'txt:data'},{'mod:data'},{'txt:data'}] ?
        // = > json doc
        let r = /\*(\d)\*/g;
        let logs = document.getElementById('logs');
        data.logs.forEach((log) => {
            let div = document.createElement('div');
            for (var key in log) {
                let src = this.getUser(parseInt(key));
                let img = document.createElement('img');
                img.src = src;
                div.appendChild(img);

                let split_message = log[key].split(r);
                split_message.forEach((mess) => {
                    let user_mod;
                    if (mess.length == 1) {
                        user_mod = this.getUser(parseInt(mess));
                    }
                    if (user_mod) {
                        let img = document.createElement('img');
                        img.src = user_mod;
                        div.appendChild(img);
                    } else {
                        // Todo bad spacing here, use css
                        let textnode = document.createTextNode(' ' + mess);
                        div.appendChild(textnode);
                    }
                });
            }
            logs.appendChild(div);
        });
        while (logs.childElementCount >= MAX_LOG) {
            logs.removeChild(logs.childNodes[0]);
        }
        logs.scrollTop = logs.scrollHeight;
    }

    onMap(data) {
        if (data.explosion) this.drawExplosions(data.explosion);
        if (data.bomb) this.drawBombs(data.bomb);
        if (data.wall) this.drawWalls(data.wall);
        if (data.user) this.drawUsers(data.user);
        if (data.entity) this.drawGrass(data.entity);
    }
}

new Game();