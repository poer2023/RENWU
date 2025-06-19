// Simple test script to check frontend functionality
const http = require('http');

function makeRequest(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Test-Script'
      }
    };

    if (data && method === 'POST') {
      const postData = JSON.stringify(data);
      options.headers['Content-Length'] = Buffer.byteLength(postData);
    }

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: body
        });
      });
    });

    req.on('error', (e) => {
      reject(e);
    });

    if (data && method === 'POST') {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

async function testFrontendAPIs() {
  console.log('Testing frontend APIs...\n');
  
  try {
    // Test 1: Get tasks through frontend proxy
    console.log('1. Testing GET /api/tasks/ through frontend...');
    const tasksResponse = await makeRequest('http://localhost:3000/api/tasks/');
    console.log('Status:', tasksResponse.statusCode);
    
    if (tasksResponse.statusCode === 200) {
      const tasks = JSON.parse(tasksResponse.body);
      console.log('Tasks count:', tasks.length);
      if (tasks.length > 0) {
        console.log('First task:', {
          id: tasks[0].id,
          title: tasks[0].title,
          urgency: tasks[0].urgency
        });
      }
    } else {
      console.log('Error body:', tasksResponse.body);
    }
    
    console.log('\n2. Testing POST /api/tasks/ (create new task)...');
    const newTask = {
      title: 'API测试任务',
      description: '通过脚本创建的测试任务',
      urgency: 1
    };
    
    const createResponse = await makeRequest('http://localhost:3000/api/tasks/', 'POST', newTask);
    console.log('Create status:', createResponse.statusCode);
    
    if (createResponse.statusCode === 200) {
      const createdTask = JSON.parse(createResponse.body);
      console.log('Created task:', {
        id: createdTask.id,
        title: createdTask.title,
        urgency: createdTask.urgency
      });
      
      // Test 3: Get tasks again to verify
      console.log('\n3. Re-testing GET /api/tasks/ after creation...');
      const tasksResponse2 = await makeRequest('http://localhost:3000/api/tasks/');
      if (tasksResponse2.statusCode === 200) {
        const tasks2 = JSON.parse(tasksResponse2.body);
        console.log('New tasks count:', tasks2.length);
        const newlyCreated = tasks2.find(t => t.id === createdTask.id);
        console.log('Newly created task found:', !!newlyCreated);
      }
    } else {
      console.log('Create error body:', createResponse.body);
    }
    
    console.log('\n4. Testing frontend main page...');
    const pageResponse = await makeRequest('http://localhost:3000/');
    console.log('Main page status:', pageResponse.statusCode);
    console.log('Content-Type:', pageResponse.headers['content-type']);
    console.log('Page size:', pageResponse.body.length, 'bytes');
    
    // Check if page contains expected Vue app elements
    const hasVueApp = pageResponse.body.includes('id="app"');
    const hasTaskWall = pageResponse.body.toLowerCase().includes('taskwall');
    console.log('Contains Vue app element:', hasVueApp);
    console.log('Contains TaskWall text:', hasTaskWall);
    
  } catch (error) {
    console.error('Test failed:', error.message);
  }
}

testFrontendAPIs(); 