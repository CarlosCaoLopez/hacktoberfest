// MongoDB initialization script for drone data
// This script runs automatically when MongoDB container starts for the first time

// Switch to the drone_dispatch database
db = db.getSiblingDB('drone_dispatch');

// Create admin user with read/write access to drone_dispatch database
db.createUser({
  user: 'root',
  pwd: 'hacktoberfest',
  roles: [
    {
      role: 'readWrite',
      db: 'drone_dispatch'
    }
  ]
});

// Drone data to insert
const dronesData = [
  {
    "serial_number": "DRN-HW-001",
    "model": "Heavyweight",
    "weight_limit": 500,
    "battery_capacity": 100,
    "state": "IDLE",
    "medications": []
  },
  {
    "serial_number": "DRN-MW-002",
    "model": "Middleweight",
    "weight_limit": 300,
    "battery_capacity": 85,
    "state": "IDLE",
    "medications": []
  },
  {
    "serial_number": "DRN-LW-003",
    "model": "Lightweight",
    "weight_limit": 150,
    "battery_capacity": 15,
    "state": "IDLE",
    "medications": []
  },
  {
    "serial_number": "DRN-CW-004",
    "model": "Cruiserweight",
    "weight_limit": 400,
    "battery_capacity": 70,
    "state": "LOADING",
    "medications": []
  },
  {
    "serial_number": "DRN-MW-005",
    "model": "Middleweight",
    "weight_limit": 250,
    "battery_capacity": 55,
    "state": "DELIVERING",
    "medications": []
  },
  {
    "serial_number": "DRN-HW-006",
    "model": "Heavyweight",
    "weight_limit": 500,
    "battery_capacity": 30,
    "state": "RETURNING",
    "medications": []
  },
  {
    "serial_number": "DRN-LW-007",
    "model": "Lightweight",
    "weight_limit": 200,
    "battery_capacity": 25,
    "state": "IDLE",
    "medications": []
  },
  {
    "serial_number": "DRN-CW-008",
    "model": "Cruiserweight",
    "weight_limit": 350,
    "battery_capacity": 95,
    "state": "IDLE",
    "medications": []
  },
  {
    "serial_number": "DRN-MW-009",
    "model": "Middleweight",
    "weight_limit": 300,
    "battery_capacity": 40,
    "state": "LOADED",
    "medications": []
  },
  {
    "serial_number": "DRN-LW-010",
    "model": "Lightweight",
    "weight_limit": 100,
    "battery_capacity": 100,
    "state": "DELIVERED",
    "medications": []
  },
  {
    "serial_number": "DRN-LW-011",
    "model": "Lightweight",
    "weight_limit": 300,
    "battery_capacity": 20,
    "state": "LOADING",
    "medications": []
  }
];

// Insert drone data into the drones collection
try {
  const result = db.drones.insertMany(dronesData);
  print(`Successfully inserted ${result.insertedIds.length} drones into the database.`);

  // Log the inserted drones
  dronesData.forEach((drone, index) => {
    print(`Inserted drone ${index + 1}: ${drone.serial_number} (${drone.model}) - ${drone.state}`);
  });

} catch (error) {
  print(`Error inserting drone data: ${error}`);
}

// Verify the insertion by counting documents
const droneCount = db.drones.countDocuments();
print(`Total drones in database: ${droneCount}`);

// Create index on serial_number for better performance
try {
  db.drones.createIndex({ "serial_number": 1 }, { unique: true });
  print("Created unique index on serial_number field.");
} catch (error) {
  print(`Error creating index: ${error}`);
}

print("MongoDB initialization completed successfully!");