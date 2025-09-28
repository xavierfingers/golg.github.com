const dino = document.getElementById('dino');
const obstacle = document.getElementById('obstacle');
const scoreDisplay = document.getElementById('score');
const gameOverMessage = document.getElementById('game-over-message');
const restartBtn = document.getElementById('restart-btn');

let score = 0;
let isJumping = false;
let isGameOver = false;

function jump() {
    if (!isJumping) {
        isJumping = true;
        dino.classList.add('jump');
        setTimeout(() => {
            dino.classList.remove('jump');
            isJumping = false;
        }, 500);
    }
}

document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !isGameOver) {
        jump();
    }
});

function updateScore() {
    score++;
    scoreDisplay.textContent = `Score: ${score}`;
}

function checkCollision() {
    const dinoRect = dino.getBoundingClientRect();
    const obstacleRect = obstacle.getBoundingClientRect();

    if (
        dinoRect.right > obstacleRect.left &&
        dinoRect.left < obstacleRect.right &&
        dinoRect.bottom > obstacleRect.top
    ) {
        endGame();
    }
}

function endGame() {
    isGameOver = true;
    obstacle.style.animationPlayState = 'paused';
    gameOverMessage.classList.remove('hidden');
}

function restartGame() {
    isGameOver = false;
    score = 0;
    scoreDisplay.textContent = 'Score: 0';
    obstacle.style.animationPlayState = 'running';
    obstacle.style.animation = 'moveObstacle 2s linear infinite';
    gameOverMessage.classList.add('hidden');
}

restartBtn.addEventListener('click', restartGame);

function gameLoop() {
    if (!isGameOver) {
        updateScore();
        checkCollision();
        requestAnimationFrame(gameLoop);
    }
}

// Start the game
gameLoop();
