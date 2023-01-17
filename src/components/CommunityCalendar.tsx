import React from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import icalendarPlugin from "@fullcalendar/icalendar";

const CommunityCalendar: React.FunctionComponent = () => {
    return (
        <FullCalendar
            slotDuration="00:15:00"
            slotMinTime="09:00:00"
            slotMaxTime="18:00:00"
            navLinks={true}
            nowIndicator={true}
            height={"auto"}
            expandRows={false}
            plugins={[
                dayGridPlugin,
                timeGridPlugin,
                icalendarPlugin,
                interactionPlugin,
            ]}
            initialView="timeGridWeek"
            weekends={false}
            events={{
                url: "https://sovereigncloudstack.github.io/calendar/scs.ics",
                format: "ics",
            }}
            headerToolbar={{
                left: "prev,next today",
                center: "title",
                right: "timeGridDay,timeGridWeek,dayGridMonth",
            }}
        />
    );
};

export default CommunityCalendar;
