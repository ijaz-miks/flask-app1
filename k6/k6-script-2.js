import http from 'k6/http';
import { sleep, check, fail } from 'k6';
import { b64encode } from 'k6/encoding';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
    stages: [
        { duration: '30s', target: 20 }, // Ramp up to 20 virtual users over 30 seconds
        { duration: '15m', target: 50 },  // Stay at 50 users for 15 minutes, adjust if needed
        { duration: '30s', target: 0 },  // Ramp down to 0 users
    ],
    thresholds: {
        http_req_duration: ['p(95)<1000'], // 95% of requests should be below 1000ms
        http_req_failed: ['rate<0.05'],   // Error rate should be less than 5%
    },
};

const BASE_URL_API_GATEWAY = 'https://flask-app1.cave-jarvis.com';
const BASE_URL_INVENTORY = 'https://inventory.cave-jarvis.com';
const BASE_URL_USER = 'https://user.cave-jarvis.com';

// Function to generate random item data
function generateRandomItem() {
    const items = [
        { name: 'Item A', quantity: randomIntBetween(1, 20), price: parseFloat((Math.random() * 100).toFixed(2)) },
        { name: 'Item B', quantity: randomIntBetween(1, 50), price: parseFloat((Math.random() * 50).toFixed(2)) },
        { name: 'Item C', quantity: randomIntBetween(5, 30), price: parseFloat((Math.random() * 75).toFixed(2)) },
        { name: 'Item D', quantity: randomIntBetween(2, 15), price: parseFloat((Math.random() * 200).toFixed(2)) },
        { name: 'Item E', quantity: randomIntBetween(10, 40), price: parseFloat((Math.random() * 30).toFixed(2)) },
    ];
    return items[randomIntBetween(0, items.length - 1)];
}

// Function to generate random user data
function generateRandomUser() {
    const firstNames = ['John', 'Jane', 'Mike', 'Emily', 'David', 'Sarah'];
    const lastNames = ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones'];
    const domains = ['example.com', 'test.com', 'mail.com', 'domain.net'];

    const firstName = firstNames[randomIntBetween(0, firstNames.length - 1)];
    const lastName = lastNames[randomIntBetween(0, lastNames.length - 1)];
    const domain = domains[randomIntBetween(0, domains.length - 1)];

    return {
        name: `${firstName} ${lastName}`,
        email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${domain}`,
    };
}

// Function to get existing user IDs from the user service
function getExistingUserIds() {
    const res = http.get(`${BASE_URL_USER}/users`);
    if (res.status === 200) {
        const userIds = res.json().users.map(user => user.id);
        return userIds;
    }
    console.error(`Failed to get user IDs: ${res.status} - ${res.body}`);
    return [];
}

// Function to get existing item IDs from the inventory service
function getExistingItemIds() {
    const res = http.get(`${BASE_URL_INVENTORY}/items`);
    if (res.status === 200) {
        const itemIds = res.json().items.map(item => item.id);
        return itemIds;
    }
    console.error(`Failed to get item IDs: ${res.status} - ${res.body}`);
    return [];
}

// Functions to perform actions on services
function addInventoryItem() {
    const item = generateRandomItem();
    const res = http.post(`${BASE_URL_INVENTORY}/items`, JSON.stringify(item), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, { 'add item status is 201': (r) => r.status === 201 });
}

function createUsers() {
    const user = generateRandomUser();
    const res = http.post(`${BASE_URL_USER}/users`, JSON.stringify(user), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, { 'create user status is 201': (r) => r.status === 201 });
}

function getUsers() {
    const res = http.get(`${BASE_URL_USER}/users`);
    check(res, { 'get users status is 200': (r) => r.status === 200 });
}

function placeOrder() {
    const existingUserIds = getExistingUserIds();
    const existingItemIds = getExistingItemIds();

    if (existingUserIds.length === 0 || existingItemIds.length === 0) {
        console.warn('Skipping placeOrder due to lack of users or items');
        return;
    }

    const userId = randomItem(existingUserIds);
    const items = [{ item_id: randomItem(existingItemIds), quantity: randomIntBetween(1, 5) }];

    const res = http.post(`${BASE_URL_API_GATEWAY}/place_order`, JSON.stringify({
        user_id: userId,
        items: items
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Basic ${b64encode('user1:pass1')}`
        },
    });

    check(res, {
        'place order status is 201': (r) => r.status === 201,
        'place order duration is ok': (r) => r.timings.duration < 500
    });
}

// Function to simulate placing an order with an invalid user ID
function placeInvalidUserOrder() {
    const invalidUserId = 999999; // An ID that should not exist
    const res = http.post(`${BASE_URL_API_GATEWAY}/place_order`, JSON.stringify({
        user_id: invalidUserId,
        items: [
            { item_id: randomIntBetween(1, 5), quantity: randomIntBetween(1, 5) },
        ]
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Basic ${b64encode('user1:pass1')}`
        },
    });
    check(res, {
        'place order with invalid user status is 400': (r) => r.status === 400
    });
}

// Function to simulate placing an order with an invalid item ID
function placeInvalidItemOrder() {
    const existingUserIds = getExistingUserIds();

    if (existingUserIds.length === 0) {
        console.warn('Skipping placeInvalidItemOrder due to lack of users');
        return;
    }

    const userId = randomItem(existingUserIds);
    const invalidItemId = 999999; // An item ID that should not exist
    const res = http.post(`${BASE_URL_API_GATEWAY}/place_order`, JSON.stringify({
        user_id: userId,
        items: [
            { item_id: invalidItemId, quantity: randomIntBetween(1, 5) },
        ]
    }), {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Basic ${b64encode('user1:pass1')}`
        },
    });
    check(res, {
        'place order with invalid item status is 500': (r) => r.status === 500
    });
}

function login() {
    const res = http.post(`${BASE_URL_API_GATEWAY}/login`, JSON.stringify({
        username: 'user1',
        password: 'pass1'
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, { 'login status is 200': (r) => r.status === 200 });
}

function getItems() {
    const res = http.get(`${BASE_URL_API_GATEWAY}/items`, null, {
        headers: {
            'Authorization': `Basic ${b64encode('user1:pass1')}`
        },
    });
    check(res, { 'get items status is 200': (r) => r.status === 200 });
}

// Main function to randomly call other functions
export default function () {
    // Array of functions to be called randomly
    const actions = [
        addInventoryItem,
        createUsers,
        getUsers,
        placeOrder,
        placeInvalidUserOrder,
        placeInvalidItemOrder,
        login,
        getItems
    ];

    // Randomly select a function to execute
    const randomIndex = randomIntBetween(0, actions.length - 1);
    actions[randomIndex]();

    sleep(1); // Sleep for 1 second
}
