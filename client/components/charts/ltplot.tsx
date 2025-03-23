'use client'

import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

import axios from 'axios';

const LatencyTimePlot = () => {
    const {user} = useUser();

    if (!user) {
        return;
    }

    useEffect(() => {
        // fetch data
        const fetchData = async () => {
            try {
                const res = await axios.get(`http://localhost:8000/storage/latest/${user.id}`)
                console.log(res.data);
            }catch {
                console.error("Error fetching data");
            }
        }
        fetchData();
    }, []);

    return (
        <div>
            Page
        </div>
    );
}

export default LatencyTimePlot;