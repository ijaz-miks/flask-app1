import http from 'k6/http';
import { sleep, check } from 'k6';
import { b64encode } from 'k6/encoding';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
    scenarios: {
        random_requests: {
            executor: 'constant-arrival-rate',
            rate: 50,   // Adjust to control the request rate (requests per second)
            timeUnit: '1s',
            duration: '15m',
            preAllocatedVUs: 10, // Adjust based on your expected load
            maxVUs: 50,
        },
    },
    thresholds: {
        http_req_failed: ['rate<0.05'], // Error rate should be less than 5%
        http_req_duration: ['p(95)<1000'], // 95th percentile of request duration should be less than 1 second
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
    const res = http.post(`${BASE_URL_API_GATEWAY}/place_order`, JSON.stringify({
        user_id: randomIntBetween(1, 5), // Assuming you have at least 5 users
        items: [
            { item_id: randomIntBetween(1, 5), quantity: randomIntBetween(1, 5) }, // Assuming you have at least 5 items
        ]
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

// Function to simulate different issue types
function introduceIssue(issueType) {
    if (issueType === 'HighErrorRate') {
        // Simulate a high error rate by making requests that are likely to fail
        const res = http.get(`${BASE_URL_API_GATEWAY}/error`); // Assuming you have an /error endpoint that returns a 500 error
        check(res, { 'Error Rate Increased': (r) => r.status >= 500 });

    } else if (issueType === 'ErrorRateSuddenIncrease') {
        // Simulate a sudden increase in error rate
        for (let i = 0; i < 5; i++) {
            const res = http.get(`${BASE_URL_API_GATEWAY}/error`); // Assuming you have an /error endpoint that returns a 500 error
            check(res, { 'Error Rate Increased': (r) => r.status >= 500 });
        }

    } else if (issueType === 'HighLatency') {
        // Simulate high latency by making requests to a slow endpoint
        const res = http.get(`${BASE_URL_API_GATEWAY}/slow`); // Assuming you have a /slow endpoint that introduces a delay
        check(res, { 'Latency Increased': (r) => r.timings.duration > 1000 });

    } else if (issueType === 'LatencyAnomaly') {
        // Simulate a gradual latency increase
        sleep(randomIntBetween(1, 3)); // Introduce a delay that increases over time
        const res = http.get(`${BASE_URL_API_GATEWAY}/items`);
        check(res, { 'Latency Anomaly': (r) => r.timings.duration > 500 });

    } else if (issueType === 'CrashPods') {
        // Simulate a pod crash (requires access to Kubernetes API)
        // This is an advanced scenario and requires careful consideration
        // You might need to use a separate script or tool to interact with the Kubernetes API
        console.log('Simulating pod crash - not implemented in this example');

    } else {
        console.error(`Unknown issue type: ${issueType}`);
    }
}

// Main function to randomly call other functions
export default function () {
    // Decide whether to introduce an issue or perform normal actions
    const introduceIssueFlag = randomIntBetween(1, 100); // e.g., 20% chance to introduce an issue

    if (introduceIssueFlag <= 20) {
        // Select a random issue type
        const issueTypes = ['HighErrorRate', 'ErrorRateSuddenIncrease', 'HighLatency', 'LatencyAnomaly', 'CrashPods'];
        const selectedIssue = randomItem(issueTypes);

        console.log(`Introducing issue: ${selectedIssue}`);
        introduceIssue(selectedIssue);
    } else {
        // Array of functions to be called randomly
        const actions = [
            addInventoryItem,
            createUsers,
            getUsers,
            placeOrder,
            login,
            getItems
        ];

        // Randomly select a function to execute
        const randomIndex = randomIntBetween(0, actions.length - 1);
        actions[randomIndex]();
    }

    sleep(randomIntBetween(1, 3)); // Sleep for a random time between 1-3 seconds
}