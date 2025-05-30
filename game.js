const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas(); // Initial resize

// Keyboard state
const keys = {};
window.addEventListener('keydown', function(e) { keys[e.code] = true; });
window.addEventListener('keyup', function(e) { keys[e.code] = false; });

// Skateboarder class
class Skateboarder {
    constructor(x, y, width, height, color) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;

        this.dx = 0; // horizontal velocity
        this.dy = 0; // vertical velocity
        this.jumpStrength = 16; // Adjusted for more noticeable jump
        this.gravity = 0.8;
        this.isJumping = false;
        this.groundY = canvas.height - this.height - groundOffset;
        this.direction = 1; // 1 for right, -1 for left
        this.shotRecently = false;
    }

    shoot() {
        const bulletWidth = 10;
        const bulletHeight = 5;
        const bulletSpeed = 7;
        const bulletColor = 'yellow';
        // Calculate starting x based on player direction
        let bulletX = this.direction === 1 ? this.x + this.width : this.x - bulletWidth;
        const bulletY = this.y + this.height / 2 - bulletHeight / 2; // Middle of player
        bullets.push(new Bullet(bulletX, bulletY, bulletWidth, bulletHeight, bulletColor, bulletSpeed, this.direction));
    }

    update() {
        // Horizontal Movement
        if (keys['ArrowLeft']) {
            this.dx = -5;
            this.direction = -1;
        } else if (keys['ArrowRight']) {
            this.dx = 5;
            this.direction = 1;
        } else {
            this.dx *= 0.9; // Damping
        }

        // Jumping
        if (keys['Space'] && !this.isJumping) {
            this.dy = -this.jumpStrength;
            this.isJumping = true;
        }

        // Apply Velocities
        this.x += this.dx;
        this.y += this.dy;

        // Apply Gravity
        // A more robust check: if the bottom of the player is above groundY
        if (this.y + this.height < this.groundY + this.height || this.isJumping) {
            this.dy += this.gravity;
        }

        // Ground Collision
        if (this.y > this.groundY) {
            this.y = this.groundY;
            this.dy = 0;
            this.isJumping = false;
        }

        // Screen Boundaries
        if (this.x < 0) {
            this.x = 0;
        }
        if (this.x + this.width > canvas.width) {
            this.x = canvas.width - this.width;
        }
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);
    }
}

// Create player instance
let player;
const playerWidth = 50;
const playerHeight = 100;
const groundOffset = 20; // Distance from bottom of the canvas

function initializePlayer() {
    const initialX = canvas.width / 2 - playerWidth / 2;
    const initialY = canvas.height - playerHeight - groundOffset;
    if (player) {
        // If player exists, update its properties
        player.x = initialX;
        player.y = initialY;
        player.groundY = canvas.height - player.height - groundOffset;
        player.isJumping = false; // Reset jumping state
        player.dx = 0;
        player.dy = 0;
    } else {
        player = new Skateboarder(
            initialX,
            initialY,
            playerWidth,
            playerHeight,
            'blue'
        );
    }
    player.groundY = canvas.height - player.height - groundOffset; // Ensure groundY is set
}

// Zombie class
class Zombie {
    constructor(x, y, width, height, speed) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.speed = speed;
        this.color = 'green';
    }

    update() {
        this.x -= this.speed; // Move from right to left
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);
    }
}

// Game elements
let zombies = [];
const ZOMBIE_DEFAULT_WIDTH = 40; // Using constants for clarity
const ZOMBIE_DEFAULT_HEIGHT = 90;

// Zombie Spawning
let zombieSpawnTimer = 0;
let zombieSpawnInterval = 180; // Approx 3 seconds at 60FPS

function spawnZombie() {
    const x = canvas.width; // Start off-screen right
    // Ensure player and player.groundY are available
    const y = (player ? player.groundY + player.height - ZOMBIE_DEFAULT_HEIGHT : canvas.height - ZOMBIE_DEFAULT_HEIGHT - groundOffset);
    const speed = 1 + Math.random() * 2; // Random speed between 1 and 3
    zombies.push(new Zombie(x, y, ZOMBIE_DEFAULT_WIDTH, ZOMBIE_DEFAULT_HEIGHT, speed));
}

// Bullet Class
class Bullet {
    constructor(x, y, width, height, color, speed, direction) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
        this.speed = speed;
        this.direction = direction; // 1 for right, -1 for left
    }

    update() {
        this.x += this.speed * this.direction;
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);
    }
}
let bullets = [];


function initializeGameElements() {
    initializePlayer();
    zombies = []; // Clear existing zombies
    bullets = []; // Clear existing bullets
    zombieSpawnTimer = 0; // Reset spawn timer
    // Optionally, spawn one initial zombie or wait for timer
    // spawnZombie(); 
}


initializeGameElements(); // Initialize player, clear zombies and bullets

// Adjust game elements on resize
window.addEventListener('resize', () => {
    resizeCanvas(); // Resize canvas first
    // Re-initialize player, which also sets its groundY correctly.
    // Zombies will be cleared and spawning will continue based on the new canvas size.
    initializeGameElements(); 
});


function update() {
    // Game logic will go here
    if (player) {
        player.update();
        // Shooting input
        if (keys['KeyX'] && !player.shotRecently) {
            player.shoot();
            player.shotRecently = true;
            setTimeout(() => {
                if (player) player.shotRecently = false;
            }, 250); // Cooldown in ms
        }
    }

    // Update bullets
    bullets.forEach(bullet => {
        bullet.update();
    });

    // Remove off-screen bullets
    bullets = bullets.filter(bullet => bullet.x > 0 && bullet.x + bullet.width < canvas.width);


    // Zombie spawning
    zombieSpawnTimer++;
    if (zombieSpawnTimer >= zombieSpawnInterval) {
        spawnZombie();
        zombieSpawnTimer = 0;
        // Optional: Randomize next spawn interval
        zombieSpawnInterval = 120 + Math.random() * 120; // e.g., between 2 and 4 seconds
    }

    // Update zombies
    zombies.forEach(zombie => {
        zombie.update();
    });

    // Remove off-screen zombies
    zombies = zombies.filter(zombie => zombie.x + zombie.width > 0);

    // Collision detection: Bullets vs Zombies
    for (let i = bullets.length - 1; i >= 0; i--) {
        for (let j = zombies.length - 1; j >= 0; j--) {
            const bullet = bullets[i];
            const zombie = zombies[j];

            // Ensure bullet and zombie are valid objects before accessing properties
            if (bullet && zombie && checkCollision(bullet, zombie)) {
                bullets.splice(i, 1); // Remove the bullet
                zombies.splice(j, 1); // Remove the zombie
                // Since the bullet is gone, no need to check it against other zombies
                break; 
            }
        }
    }

    // Collision detection: Player vs Zombies
    if (player) { // Ensure player exists
        for (let i = zombies.length - 1; i >= 0; i--) {
            const zombie = zombies[i];
            if (zombie && checkCollision(player, zombie)) {
                console.log("Game Over! Player hit by a zombie.");
                // For now, just log. Future steps would handle game over state.
                // For example, by setting a flag: isGameOver = true;
                // And then potentially stopping player movement, zombie spawning, etc.
                // Or even removing the zombie: zombies.splice(i, 1);
                // For this step, logging is sufficient.
            }
        }
    }
}

// Collision detection function
function checkCollision(rect1, rect2) {
    if (!rect1 || !rect2) { // Safety check
        return false;
    }
    return rect1.x < rect2.x + rect2.width &&
           rect1.x + rect1.width > rect2.x &&
           rect1.y < rect2.y + rect2.height &&
           rect1.y + rect1.height > rect2.y;
}


function draw() {
    // Clear the canvas
    ctx.fillStyle = '#444'; // A dark gray color
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Drawing game elements will go here
    if (player) {
        player.draw(ctx);
    }
    bullets.forEach(bullet => {
        bullet.draw(ctx);
    });
    zombies.forEach(zombie => {
        zombie.draw(ctx);
    });
}

function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

// Start the game loop
gameLoop();
