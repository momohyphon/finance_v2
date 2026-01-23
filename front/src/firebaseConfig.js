import {initializeApp} from "firebase/app";
import {getFirestore} from "firebase/firestore";

const firebaseConfig = {
apikey:"AIzaSyBXvWomUKQVviH0R9bWl7HVm0Vucyw8EE8",
authDomain: "myapp-fc7e4.firebaseapp.com",
projectId:"myapp-fc7e4",
storageBucket:"myapp-fc7e4.firebasestorage.app",
messagingSenderId:"421474261694",
appId:"1:421474261694:web:5543c4b8dc70f68e5a5cef",
measurementId: "G-JG9HM7PK7Z"
};


const app = initializeApp(firebaseConfig);


export const db = getFirestore(app);